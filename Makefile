# Neurex IDE — Makefile
# Usage: make <target>
.PHONY: up down build logs shell-api shell-web sandbox clean nuke dev-api dev-web

# ── Primary targets ───────────────────────────────────────────────────────────

## Start all services (detached)
up:
	docker compose up -d
	@echo ""
	@echo "✅ Neurex is starting."
	@echo "   IDE:  http://localhost:3000"
	@echo "   API:  http://localhost:8000/docs"
	@echo "   Logs: make logs"

## Stop all services
down:
	docker compose down

## Rebuild all images (use after changing Dockerfiles or requirements)
build:
	docker compose build --no-cache

## Tail logs for all services
logs:
	docker compose logs -f

## Tail logs for a specific service: make logs-api
logs-%:
	docker compose logs -f $*

## Rebuild and restart a single service: make restart-neurex-api
restart-%:
	docker compose up -d --build $*

# ── Dev shells ────────────────────────────────────────────────────────────────

## Open a shell inside the API container
shell-api:
	docker compose exec neurex-api bash

## Open a shell inside the web container
shell-web:
	docker compose exec neurex-web sh

## Open Ollama CLI
shell-ollama:
	docker compose exec ollama bash

# ── Sandbox ───────────────────────────────────────────────────────────────────

## Build the tester sandbox image
sandbox:
	bash scripts/build-sandbox.sh

## Test the sandbox is working
sandbox-test:
	docker run --rm --network none \
		-v $(PWD)/workspace:/workspace:ro \
		neurex-sandbox:latest \
		python -c "print('Sandbox OK')"

# ── Local dev (no Docker) ─────────────────────────────────────────────────────

## Run API locally with hot reload (requires Python 3.12+ and pip install)
dev-api:
	cd neurex-api && PATH="../neurex-web/node_modules/.bin:$$PATH" ./.venv/bin/uvicorn main:app --reload --host 127.0.0.1 --port 8000

## Run web locally with hot reload (requires npm install first)
dev-web:
	cd neurex-web && npm run dev

## Run BOTH api and web locally (one-liner)
dev:
	(make dev-api & make dev-web)

## Install all Python deps locally
install-api:
	cd neurex-api && pip install -r requirements.txt

## Install all JS deps locally
install-web:
	cd neurex-web && npm install

# ── Database ──────────────────────────────────────────────────────────────────

## Show task graph from SQLite
db-tasks:
	sqlite3 neurex-api/neurex.db "SELECT agent_type, title, status, iteration FROM tasknode ORDER BY created_at DESC LIMIT 20;"

## Clear all tasks and chat history (keep vector store)
db-clear:
	sqlite3 neurex-api/neurex.db "DELETE FROM tasknode; DELETE FROM chatmessage;"
	@echo "✅ Task and chat history cleared."

## Reset ChromaDB vector store (forces full re-index on next start)
db-reset-vectors:
	docker compose rm -sf chromadb
	docker volume rm $$(docker volume ls -q | grep chroma) 2>/dev/null || true
	docker compose up -d chromadb
	@echo "✅ ChromaDB reset. Re-index will run on next API startup."

# ── Cleanup ───────────────────────────────────────────────────────────────────

## Remove containers and volumes (keeps Ollama model weights)
clean:
	docker compose down -v --remove-orphans

## Full reset — removes EVERYTHING including downloaded models (slow re-download)
nuke:
	docker compose down -v --remove-orphans
	docker volume rm $$(docker volume ls -q | grep neurex) 2>/dev/null || true
	@echo "⚠️  All Neurex data removed. Model weights will re-download on next start."

# ── Testing & Quality ─────────────────────────────────────────────────────────

## Run all API tests
test:
	cd neurex-api && ./.venv/bin/python -m pytest tests/ -v --tb=short

## Run API tests with coverage
test-cov:
	cd neurex-api && ./.venv/bin/python -m pytest tests/ -v --tb=short --cov=core --cov=api --cov-report=term-missing

## Run API integration tests (unmocked daemons)
test-integration:
	cd neurex-api && ./.venv/bin/python -m pytest tests/integration/ -v --tb=short

## Lint Python (ruff) and TypeScript (eslint)
lint:
	cd neurex-api && ./.venv/bin/ruff check .
	cd neurex-web && npx eslint . --max-warnings 0
	python3 scripts/verify-docs.py

## Type check Python (pyright) and TypeScript (tsc)
typecheck:
	cd neurex-api && ./.venv/bin/pyright
	cd neurex-web && npx tsc --noEmit

## Run evals against a live API
eval:
	cd eval && python run_evals.py

## Run live evaluations with real LLM inference against local Ollama (requires running API)
test-live:
	NEUREX_MOCK_LLM=false cd eval && python run_evals.py

# ── Automation ────────────────────────────────────────────────────────────────

## Update LOC badges in README.md
loc:
	bash scripts/update-loc.sh

## Sync sanitized branch to public GitHub remote (usage: make sync-github [BRANCH=name])
sync-github:
	bash scripts/sync-github.sh $(BRANCH)

## Run tests and checks, then push to internal origin and public GitHub main
release: test-live test typecheck lint
	git push origin main
	bash scripts/sync-github.sh main

# ── Help ──────────────────────────────────────────────────────────────────────

help:
	@echo ""
	@echo "Neurex IDE — Available targets:"
	@echo ""
	@grep -E '^##' $(MAKEFILE_LIST) | sed 's/## /  /'
	@echo ""
