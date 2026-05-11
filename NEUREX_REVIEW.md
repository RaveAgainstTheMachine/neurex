# NEUREX ARCHITECTURAL REVIEW

> **Status**: v0.5.4 — Active Development
> **Last Reviewed**: 2026-05-11

## 1. Executive Summary

Neurex is a local-first AI engineering workspace composed of three services: a React frontend (`neurex-web`), a FastAPI backend (`neurex-api`), and a Rust control plane (`neurex-cli`). The project reached core feature stability in v0.5.x with working agentic orchestration, persistent terminals, distributed inference, and LAN collaboration.

This review reflects the current state of the codebase after a documentation grounding pass and dead code cleanup in v0.5.4.

## 2. Core Service Review

### 2.1 Orchestrator & Task Graph (Status: STABLE)
- **Implementation**: `core/orchestrator.py`, `core/task_graph.py`
- **What works**: User messages are decomposed into multi-step task graphs (SQLite-backed). Tasks flow through `PENDING → THINKING → EXECUTING → AWAITING_APPROVAL → DONE/FAILED`. The orchestrator supports Human-in-the-Loop approval for shell commands and filesystem mutations.
- **Coverage**: Unit tests added in v0.5.4 for task CRUD and graph isolation.
- **Known gap**: No integration test for the full WebSocket → plan → approve → execute flow yet.

### 2.2 Agent Framework (Status: STABLE)
- **Implementation**: `core/agents/base_agent.py`, plus 8 specialized agents (planner, coder, tester, researcher, reviewer, debater, commander, swarm).
- **What works**: Agents stream tokens from Ollama, dispatch tool calls via the MCP client, and enforce collaboration locks before file mutations. Context injection includes project rules, scratchpad, and RAG.
- **Known gap**: The `debater_agent.py` and `swarm_agent.py` are scaffolded but have not been validated in real multi-agent workflows.

### 2.3 Dynamic Model Routing (Status: STABLE)
- **Implementation**: `core/orchestrator.py`, `core/settings/manager.py`, frontend `InfraPanel`.
- **What works**: Cognitive roles (Planning, Coding, Reviewing) map to user-selected models at runtime. The `Orchestrator` resolves the correct model for each agent type through a centralized routing registry. Users can swap models per-role in the UI.

### 2.4 Terminal Persistence (Status: STABLE)
- **Implementation**: `core/terminal/pty_manager.py`, frontend `Terminal` component.
- **What works**: PTY sessions survive browser refresh. Output is buffered server-side and replayed on reconnect. Sessions are scoped to conversation contexts.

### 2.5 RAG / Codebase Indexing (Status: STABLE)
- **Implementation**: `core/memory/worker.py`, `core/memory/chunker.py`, `core/memory/embedder.py`.
- **What works**: File watcher detects changes, Tree-Sitter parses code into chunks, local embedding models generate vectors, and ChromaDB stores them. Agents query this index before execution for project context.

### 2.6 Mesh & Distributed Inference (Status: FUNCTIONAL, NICHE)
- **Implementation**: `core/infrastructure/mesh.py`, `core/infrastructure/distributed.py`, `core/infrastructure/vram_pool.py`.
- **What works**: Peer discovery, node telemetry monitoring, and routing inference requests to the best available node. VRAM pooling tracks capacity across LAN nodes. The `llama-rpc-server` integration enables tensor splitting across machines.
- **Known gap**: No automated tests. This is a power-user feature with limited adoption.

### 2.7 Security & Collaboration (Status: STABLE)
- **Implementation**: `core/security/`, `core/collaboration/`, `core/infrastructure/firewall.py`.
- **What works**: JWT authentication, mTLS for LAN traffic, Docker sandboxing for agent-generated code, SSRF protection, path traversal mitigation, command injection prevention via positional args. Collaboration locks prevent concurrent write collisions.

### 2.8 Rust Control Plane (Status: STABLE)
- **Implementation**: `neurex-cli/src/` (6 files, ~1,250 LOC).
- **What works**: Auto-provisions a hermetic Python environment via `uv`. Manages the lifecycle of the API and web services. Provides HTTPS with auto-redirect and reverse proxy with `X-Forwarded-*` header propagation.

### 2.9 CI/CD (Status: OPERATIONAL)
- **Implementation**: `.github/workflows/` (main.yml, release.yml, codeql.yml).
- **What works**: GitHub Actions pipeline for Docker Hub builds (API, Web, Sandbox) and multi-platform CLI binary distribution. CodeQL scanning enabled. Dependabot configured for npm and GitHub Actions.
- **Known gap**: Tests are not yet gated in CI. The `make test` target was added in v0.5.4 and should be integrated into `main.yml`.

## 3. Quarantined Code (v0.5.4 Cleanup)

During the v0.5.4 review, **23 backend modules** and **6 API routes** were moved to `_quarantine/` directories. These modules were either:
- Never imported by any active code path (0 inbound references), or
- Only referenced by other dead modules in a circular chain, or
- Speculative implementations from earlier sprint phases with no real backing functionality.

**Quarantined infrastructure modules** (23 files):
`attention_pool`, `gradient_hub`, `hardware_orchestrator`, `heartbeat_agent`, `privacy_guard`, `rbac`, `worktree_manager`, `quantum_sim`, `temporal`, `neural_law`, `substrate_sync`, `self_optimizer`, `goal_generator`, `plugin_gen`, `inceptor`, `kv_sync`, `neural_swap`, `quantizer`, `weight_sync`, `distiller`, `knowledge_base`, `live_reloader`, `adapter_orchestrator`.

**Quarantined routes** (6 files):
`singularity`, `synthesis`, `temporal`, `consensus`, `evolution`, `voice`.

These files are preserved in `_quarantine/` directories and can be restored if their features become development priorities.

## 4. Technical Debt & Known Risks

| Area | Risk | Status |
|:---|:---|:---|
| **Test coverage** | Near-zero until v0.5.4. Task graph tests added; orchestrator and agent tests still needed. | 🟡 In progress |
| **Frontend speculative panels** | ~7 dashboard components (SingularityDashboard, TemporalDashboard, etc.) may be orphaned from quarantined routes. | 🟡 Needs audit |
| **Eval framework** | 15 test cases scaffolded but never executed against a live model. No baseline score exists. | 🔴 Unvalidated |
| **SQLite at scale** | Single-file DB is fine for single-user, but may bottleneck under concurrent multi-agent workloads. | 🟢 Low risk for now |
| **Swarm consensus** | The voting system in `core/collaboration/consensus.py` is wired but untested in real multi-agent scenarios. | 🟡 Needs validation |

## 5. Recommendations

1. **Gate CI on tests**: Add `make test` to the GitHub Actions `main.yml` pipeline.
2. **Run evals**: Execute `eval/run_evals.py` against a real model and establish a baseline score.
3. **Audit frontend panels**: Remove or quarantine dashboard components that depend on quarantined backend routes.
4. **Build the Security Sentinel**: This is the highest-impact differentiator — a background agent that scans for `shell=True`, path traversals, and command injection.
5. **Delete quarantine**: After 30 days with no regressions, permanently delete the `_quarantine/` directories.

---
*Reviewed 2026-05-11. Reflects codebase state at v0.5.4.*
