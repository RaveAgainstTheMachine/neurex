# Neurex System Capabilities & Reality Manifest

This document outlines the exact implementation state of all subsystems in Neurex `v0.15.1`. It distinguishes between fully functional production layers, mocked/simulated developmental features, and quarantined dead code to bridge the gap between architectural aspirations and the current codebase reality.

---

## 1. System Implementation Summary

| Subsystem | Folder / File | Implementation State | Verification Method |
| :--- | :--- | :--- | :--- |
| **Rust Control Plane** | `neurex-cli/src/` | **PRODUCTION READY** | Managed via standard Rust tests and doctor command |
| **FastAPI Backend** | `neurex-api/` | **PRODUCTION READY** | Pytest suite (`make test`) |
| **Monaco IDE UI** | `neurex-web/src/` | **PRODUCTION READY** | React component checks / Playwright |
| **Task Graph** | `core/task_graph.py` | **PRODUCTION READY** | Persistent SQLite DB writes |
| **PTY Terminal Manager** | `core/terminal/` | **PRODUCTION READY** | Decoupled background subprocesses |
| **WASI Sandbox** | `neurex-cli/src/wasi_sandbox.rs` | **PRODUCTION READY** | WASM binary executions with pipe capture |
| **Docker Sandbox** | `neurex-cli/src/sandbox.rs` | **PARTIAL** | Bollard API wrapper (Disabled by default) |
| **ChromaDB / Memory** | `core/memory/` | **FUNCTIONAL (LOCAL)** | Watchdog file changes to ChromaDB |
| **Plugin Hub / Marketplace** | `core/skills/manager.py` | **MOCKED / STUBBED** | Mock local memory persistence only |
| **Multi-Agent Courtroom** | `core/agents/debater_agent.py` | **PARTIAL** | UI and logic active, but relies on Mock LLM outputs in tests |
| **Swarm P2P Mesh Sync** | `core/infrastructure/mesh.py` | **SIMULATED** | Network discovery stubs; requires manual mTLS configurations |
| **Temporal / Optimization** | `_quarantine/` | **DEPRECATED / INACTIVE** | Quarantined dead code |

---

## 2. Deep Dive: Subsystem Realities

### 2.1 Fully Implemented Subsystems (Production-Grade)

- **neurex-cli (Rust Daemon)**: Compiles into a single-file binary using Tokio. It successfully provisions standalone `uv` and Python `3.11`, configures virtual environments, runs Axum-driven reverse proxies, terminates SSL/TLS boundaries, and propagates HTTP headers transparently.
- **PTY Terminal Persistence**: The `PTYManager` spawns host-level PTY processes. Streams are buffered server-side and reconnected dynamically on UI page reloads.
- **Task Graph Persistence**: Task structures are written as SQLModel schemas into a local SQLite database (`neurex.db`), allowing execution state recovery across service restarts.
- **WASI Sandbox**: Fully implemented in Rust using `wasmtime` and `MemoryOutputPipe`. Executes compiled WASM modules and redirects guest standard input/output streams cleanly.

### 2.2 Mocked & Simulated Subsystems (Dev-Only/Mocked)

- **Plugin Hub & Local Marketplace**:
  - *Reality*: Endpoints like `/api/skills/marketplace` and `/api/skills/publish` are operational but write to a mock in-memory store in `core/skills/manager.py`. There is no global marketplace registry or repository sync; publishing acts only as a local session stub.
- **Swarm P2P Mesh Sync**:
  - *Reality*: Local network peer discovery via mTLS is implemented but relies on manual setups. The peer-to-peer VRAM pooling and hidden-state updates are not covered by automated smoke tests and run on simulated network delays.
- **Docker Sandbox**:
  - *Reality*: The `sandbox.rs` interface connects to the Docker daemon via Bollard socket configurations, but is turned off by default in standard installs. If Docker is absent, the CLI falls back silently to local execution, which leaves the host environment exposed.

### 2.3 The LLM Mocking Mechanism in Tests

The entire automated test suite (`pytest`) and evaluation harness (`run_evals.py`) runs with the environment variable:
```bash
NEUREX_MOCK_LLM=true
```
- **Why this exists**: Ensures 100% green pipelines and sub-second test execution by completely bypassing remote API or local Ollama/llama.cpp inference calls.
- **The Gap**: When `NEUREX_MOCK_LLM` is `true`, the `Orchestrator` replaces model completion calls with a simple substring replacement rule (appending `# Refactored by Mock AI` to the modified content).
- **Consequence**: The test suite guarantees that the task graph, file saving, and database queries work, but it does NOT verify that the agent can actually synthesize syntactically correct code or react to real language models.

---

## 3. Quarantined Modules (Dead Code)

Speculative future phases (Phases 45-60) and sci-fi features have been completely disabled and quarantined into:
- `neurex-api/core/infrastructure/_quarantine/`
- `neurex-api/api/routes/_quarantine/`

These modules (including `attention_pool`, `quantum_sim`, `live_reloader`, `self_optimizer`, `temporal`, `singularity`, `consensus`, and `voice`) are **dead code** and are not imported by any active system execution path.
