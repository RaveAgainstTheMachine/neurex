# Neurex Development Roadmap

This document outlines the true development trajectory of Neurex, focusing on honest reporting of functional capabilities versus planned features.

## 🛰️ Current Operational Status
- **Current Version**: `v0.16.0`
- **Status**: See [KNOWN_ISSUES.md](./KNOWN_ISSUES.md) for a complete inventory of 0-coverage modules and security gaps.

---

## 🗺️ Feature Classification

### Tier 1: Working Now (Tested & Functional)
- Monaco editor with syntax highlighting, multi-root workspaces, persistent PTY terminals
- SQLite-backed task graph engine for multi-step agent orchestration
- Agent tool calling with human-in-the-loop approval prompts
- Role-based model routing (assign different models to planning/coding/review)
- ChromaDB-backed semantic memory (RAG) for cross-session context
- LSP integration for diagnostics and completion
- Rust CLI daemon with `uv` self-provisioning
- Sanitized dual-remote git sync (Gitea full history, GitHub sanitized mirror)
- CI/CD with pytest (270 tests), ruff, eslint, clippy

### Tier 2: Built But Unvalidated (Code exists, 0% test coverage)
- P2P mesh sync over LAN (simulated only, never tested multi-device)
- Multi-agent consensus debate (opt-in, `consensus_enabled` defaults to `False`)
- Dynamic VRAM pooling via `llama-rpc-server` (niche, no real-world validation)
- Dynamic re-quantization under memory pressure
- Plugin Hub and Local Marketplace (entirely mocked stubs)
- Governance/sandbox authorization boundary (`governance.py` — 0% coverage, CodeQL-flagged)
- 16 core modules with zero test coverage (see [KNOWN_ISSUES.md](./KNOWN_ISSUES.md))

### Tier 3: Planned Features (Not yet implemented)
- [ ] End-to-end user flow smoke testing (authentication → agent code execution)
- [ ] Test coverage for all 16 zero-coverage modules
- [ ] Human security audit of `governance.py` and sandbox boundary
- [ ] Real multi-device P2P mesh testing (not simulated)
- [ ] Demo video of actual end-to-end workflow
- [ ] Unmocked Plugin Hub with real validation and persistence
- [ ] Per-session workspace isolation (replace `os.getcwd()` fallback in `governance.py`)
- [ ] Integrity score hardening (currently trivially gameable)
- [ ] Dynamic grant audit trail (currently in-memory, lost on restart)
- [ ] WASM sandbox for untrusted agent code (Docker fallback only today)
- [ ] Cross-project knowledge sharing (quarantined, no implementation)
- [ ] Automated version drift detection in CI

---

<details>
<summary><b>Historical Development Log (Legacy AI-Generated Milestones)</b></summary>

*Note: The following milestones were generated and marked complete by AI agents during earlier development phases. They represent code written, but not necessarily validated or human-tested capabilities.*

### Core Architecture
- [x] **Rust Control Plane**: Native daemon for environment provisioning and service management.
- [x] **Distributed Inference**: Multi-node tensor pooling via llama-rpc.
- [x] **Task Graph Engine**: Persistent, SQLite-backed orchestration for complex agent goals.

### Security & Collaboration
- [x] **Hermetic Platform**: Isolated execution environments via Docker and WASI.
- [x] **LAN Sovereignty**: mTLS/SSL for all mesh traffic and secure device discovery.
- [x] **Distributed Locking**: Mutation protection for collaborative engineering sessions.

### Intelligence & UX
- [x] **Dynamic Model Routing**: Decoupling of cognitive roles (Coding, Planning) from specific models.
- [x] **Neural Lens**: Inline diagnostics and Git blame integration.
- [x] **Multi-Root Workspaces**: Support for parallel project management in a single session.

### Interactive Agentic IDE (v0.6.0)
- [x] **Visual Agent Task Graph Editor**: A node-based designer canvas where users can visually rewire task dependencies, insert manual/agent steps, and set active execution breakpoints.
- [x] **Multi-Cursor AI Pair Programming**: Real-time collaborative typing in Monaco with visual AI cursors (`[Neurex Coder]`), selection highlights, and 60Hz telemetry sync.
- [x] **Bidirectional LSP Context Router**: Exposing language server operations (`find references`, `go to definition`, `diagnostics`) directly to agents to query semantic codebase relations.
- [x] **Visual MCP Tool Sandbox & Manager**: A dashboard listing connected Model Context Protocol servers with a granular permission matrix (Always Allow, Always Ask, Deny) and manual tool playgrounds.
- [x] **Interactive Simulation Benchmarks**: Real-time evaluation runs designed to test agent responsiveness and cooperation in live visual environments.
- [x] **Telemetry Replay Canvas**: An interactive debugger to record, play back, and inspect agent WebSocket events, PTY streams, and cursor selections.
- [x] **Zero-Diff Staging Guard**: Sandboxed environment checking before committing swarm mutations, ensuring 100% stable workspace rollbacks.

### Grounded Intelligence & DX (v0.7.0)
- [x] **Multi-Agent Consensus Debates**: SQLite-backed persistent debate sessions, round-robin sequencers for multi-agent arguments, and a premium glassmorphic Courtroom UI with steering and visualization dashboards.
- [x] **Clean CI/CD & Teardown Hygiene**: Hardened pytest teardown hooks by cleanly shutting down `watcher_service` and disposing of SQLAlchemy connection pools on lifespan exit, achieving 100% clean pre-release gates with zero connection leaks, unhandled thread exceptions, or warnings.
- [x] **Hermetic E2E WebSocket & Smoke Evaluations**: Added 6 new high-coverage E2E integration test scenarios to the smoke evaluation suite (`run_evals.py` and `test_smoke_evals.py`), fully verifying round-robin execution, concurrent WebSocket lock contention, and message streaming.

### Extensible Plugin Hub & Sanitized Sync (v0.8.0)
- [x] **Plugin Hub & Local Marketplace `[MOCKED/STUBBED]`**: Programmed dynamic Plugin Hub endpoints (`skills/marketplace` & `skills/publish`) with mock local persistence, duplicate prevention, and developer identity overrides.
- [x] **Unified Discovery Canvas `[MOCKED/STUBBED]`**: Designed a glassmorphic marketplace UI catalog in the browser featuring installing loaders and neon green "INSTALLED" badges synced to active registries.
- [x] **Codebase Hygiene & Purges**: Removed spec legacy directories (`SubstrateDashboard`), audited voice synthetics fallback, and eradicated all linter, formatter, typecheck, and runtime warnings/errors.
- [x] **Sanitized Dual-Remote Git Sync**: Implemented worktree-free sanitized sync logic force-pushing snapshot tags to public GitHub mirror (`github`) while keeping full development history on internal Gitea (`origin`).

### Persistent Cognitive Systems & LAN Mesh (v0.9.0)
- [x] **📡 Peer-to-Peer Mesh Sync `[SIMULATED]`**: Decentralized cross-device workspace syncing over LAN using secure TLS/mTLS without requiring central coordination. Requires manual certificates.
- [x] **🧠 Swarm Memory System (Semantic Memory)**: Vector-backed memory engine storing structural architectural conventions, patterns, and past session contexts for local cognitive recall.
- [x] **🛡️ Secure Capability Guardrails**: Upgraded runtime sandbox granting granular, secure web searches and authenticated API capabilities with real-time human confirmation.

### Dynamic Autonomy & Timeline Observability (v0.10.0)
- [x] **📈 Local Screenplay Teleplay Replay Canvas**: Chronologically visualizing and scrubbing through exact agent thought sequences during debug walkthroughs in the Flight Log panel.
- [x] **⚙️ Dynamic Autonomy Level Transition**: On-the-fly toggling of execution authority ceilings (restricted, limited, staging, full) from the UI settings and AI Panel, dynamically bound to the central Zustand store.

### Universal Automated Testing & WASM/WASI Verification (v0.11.0)
- [x] **🎭 Universal Playwright Component/E2E Testing (`neurex-web`)**: Direct browser automation checking Monaco editors, Graph editor actions, and resizable layout persistence.
- [x] **🐳 Unmocked Docker Sandbox Verification (`neurex-cli`)**: Rust integration tests executing real sandboxed PTY tasks inside Bollard containers, checking CPU/VRAM ceilings.
- [x] **📦 WASM/WASI Native Run Verification**: Validating zero-dependency `wasmtime` fallback execution planes with memory pipes.

### Self-Healing & Settings Sovereignty (v0.12.0)
- [x] **🦊 Gitea Actions CI/CD Healer `[GITEA ONLY]`**: Real `httpx`-driven polling of Gitea Actions API, auto-queueing self-healing tasks in the SQLite graph on build failure.
- [x] **🛡️ Settings Integrity Protocol**: Hardened platform settings to be 100% agnostic, enforcing the use of environment variables for local/dev infrastructure and secrets.
- [x] **⚡ High-Throughput SQLite WAL Stress Testing**: Implemented high-concurrency database logging tests to prevent WAL lock contention and verify WAL durability.

</details>

---
*Roadmap updated to reflect the v0.16.0 release.*
