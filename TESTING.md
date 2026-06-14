# Neurex QA & Testing Guidelines

This document serves as the master specification for the Neurex Quality Assurance pipeline.

## Overview
Neurex maintains an aggressive zero-trust architecture. Our tests ensure that core agents, LLM contexts, local models, and real-time backend daemons maintain high integrity during execution. 

We maintain two separate testing layers:
1. **Unit & Fast Mocked Tests** (`make test` / `make test-cov`)
2. **Unmocked Integration Tests** (`make test-integration`)

---

## 1. Unit & Fast Mocked Tests
These tests validate isolated business logic, agent decision trees, and internal utilities using a mocked `FastAPI` dependency graph.

**Key Additions (v0.15.2 Coverage Expansion):**
To eliminate 0% coverage black holes, we added robust unit coverage to core systems:
- **`test_chunker.py`**: Validates AST-aware code chunking boundaries and sliding window prose truncation.
- **`test_summarizer_agent.py`**: Ensures that historical memory compression works perfectly when context caps are reached.
- **`test_mcp_ollama.py`**: Verifies dynamic local model pulling and correct API handling of hardware offload constraints.
- **`test_terminal_tool.py`**: Ensures command safety intercepts (sandbox allowlists) and hard timeouts function correctly before execution.
- **`test_lsp_manager.py`**: Tests the asynchronous diagnostic pipeline processing JSON-RPC payloads.
- **`test_infrastructure_mesh.py`**: Validates swarm mesh node ranking and heartbeat status.
- **`test_context_scratchpad.py`**: Tests isolated ephemeral context generation during tasks.

**Execution:**
```bash
# Run all unit tests
make test

# Run unit tests and generate a terminal coverage report
make test-cov
```

---

## 2. Unmocked Integration Suite
Because Neurex operates intensive background daemons (e.g. `RPC Server`, `Firewall Manager`, `Mesh Router`, and `Memory Worker`), running `make test` using a mocked client can mask critical deadlocks.

We built a dedicated integration suite located in `tests/integration/` that boots the *actual* FastAPI lifespan sequence.

**Tests Included:**
- **`test_daemon_startup.py`**: Validates that the full `main.py` lifespan (with 12+ parallel background threads) boots smoothly without throwing runtime loop errors.
- **`test_lifespan_boot.py`**: Tests that background daemons correctly respond to internal heartbeat checks during their runtime.
- **`test_daemon_communication.py`**: Verifies inter-process communication. We test endpoints like `/api/infra/peers` and `/api/settings/firewall/apply` to prove that the event loop remains responsive while the daemons execute.

**Mocking Strategy:**
We mock ONLY commands that require Root permissions or intensive hardware usage:
- Firewalls (`netsh`/`ufw`/`pfctl`)
- Local model compilation (`llama-rpc-server`)

**Execution:**
```bash
# Run the integration suite locally
make test-integration
```
*Note on CI/CD:* Due to GitHub Actions constraints (missing GPUs, lack of unprivileged firewall access), `make test-integration` is intended to be run locally by developers prior to opening PRs. 

---

## 3. Real LLM Inference Tests (Evals)
For live evaluations against local Ollama engines, we run the non-mocked eval suite.
```bash
make test-live
```
