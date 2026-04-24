# Neurex IDE

A local-first agentic development environment. All inference runs on your
hardware via Ollama. No API keys. No cloud.

```
neurex/
├── docker-compose.yml        # Phase 1 — Infrastructure
├── ollama-entrypoint.sh      # VRAM-aware model pull on startup
├── .env.example              # Copy to .env before first run
├── .neurexrules              # Project-level agent rules
│
├── neurex-api/               # Phase 2 — Agentic Core (FastAPI)
│   ├── main.py
│   ├── core/
│   │   ├── orchestrator.py   # Supervisor — builds + runs TaskGraphs
│   │   ├── task_graph.py     # SQLite-backed DAG, loop detection
│   │   ├── agents/
│   │   │   ├── base_agent.py # Ollama streaming, tool dispatch
│   │   │   ├── planner_agent.py
│   │   │   ├── coder_agent.py
│   │   │   └── tester_agent.py
│   │   ├── mcp/
│   │   │   ├── client.py     # MCP tool dispatcher
│   │   │   └── tools/
│   │   │       ├── filesystem.py  # Path-scoped read/write/delete
│   │   │       └── terminal.py    # Sandboxed Docker exec
│   │   ├── memory/
│   │   │   ├── worker.py     # File watcher + indexing loop
│   │   │   ├── chunker.py    # AST-based tree-sitter chunking
│   │   │   └── embedder.py   # Ollama embeddings + cross-encoder reranker
│   │   └── context/
│   │       ├── manager.py    # Token budgeting, RAG retrieval, history trim
│   │       └── rules_parser.py  # .neurexrules loader + merger
│   └── api/
│       ├── websocket.py      # Streaming WS endpoint
│       └── routes/
│           ├── tasks.py
│           └── files.py
│
└── neurex-web/               # Phase 3 — UI (Next.js 14)
    └── src/
        ├── app/
        │   ├── layout.tsx
        │   ├── page.tsx      # 3-panel IDE workspace
        │   └── globals.css   # Design tokens + dark theme
        ├── components/
        │   ├── Editor/       # Monaco editor, custom Neurex theme
        │   ├── FileTree/     # Collapsible, auto-refreshing file browser
        │   ├── AgentTerminal/# Streaming chat with the agent team
        │   ├── AgentDashboard/ # Visual team status (Thinking/Writing/Testing)
        │   └── Scratchpad/   # Editable agent plan tracker
        ├── hooks/
        │   └── useWebSocket.ts  # Reconnecting WS with event dispatch
        └── lib/
            ├── store.ts      # Zustand store (messages, tasks, files)
            └── types.ts      # Shared TypeScript types
```

## Prerequisites

- Docker + Docker Compose
- NVIDIA GPU with drivers installed (CPU fallback works but is slow)
- NVIDIA Container Toolkit (for GPU passthrough)

## Quick Start

```bash
# 1. Clone and configure
cp .env.example .env
# Edit .env — at minimum set WORKSPACE_PATH to your project directory

# 2. Start everything
docker compose up

# 3. Open the IDE
open http://localhost:3000
```

On first boot, `ollama-entrypoint.sh` detects your VRAM and pulls the
appropriate model tier automatically. This takes several minutes on first run.

## Model Tiers

| VRAM       | Model                    |
|------------|--------------------------|
| ≥ 22 GB    | `deepseek-r1:32b`        |
| ≥ 10 GB    | `qwen2.5-coder:14b`      |
| < 10 GB    | `qwen2.5-coder:7b`       |

Override with `DEFAULT_MODEL=<model>` in `.env`.

## Agent Rules

Copy `.neurexrules` into your workspace directory and edit to taste.
A global `~/.neurexrules` is also supported (project rules take precedence).

## Security Notes

- The API binds to `127.0.0.1` only. Set `API_TOKEN` in `.env`.
- The tester agent runs commands inside a Docker sandbox with no network access.
- Filesystem tools are scoped to `WORKSPACE_PATH` with path traversal protection.
- File "deletes" are soft-moved to `.neurex_trash/`, never hard-deleted.

## Development

```bash
# Run API locally (no Docker)
cd neurex-api
pip install -r requirements.txt
uvicorn main:app --reload

# Run web locally
cd neurex-web
npm install
npm run dev
```
