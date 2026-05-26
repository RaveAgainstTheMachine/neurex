# Neurex Development Roadmap

This document outlines the development trajectory of Neurex, focusing on building a stable, local-first AI engineering workspace.

## 🛰️ Current Operational Status
- **Current Version**: `v0.9.0-STABLE`
- **Core Engine**: NeuralHarness v2.4
- **Status**: Stable for local and LAN-based multi-device collaboration with fully clean CI/CD gates.

---

## 🗺️ Strategy
Neurex focuses on three pillars:
1. **Local Sovereignty**: Maximum privacy and performance through local execution and distributed inference.
2. **Agentic Parity**: Enabling AI agents to work alongside humans with full tool access and persistent state.
3. **Resilient Infrastructure**: A zero-dependency, hermetic substrate that runs anywhere.

---

## ✅ Completed Milestones

### Core Architecture
- [x] **Rust Control Plane**: Native daemon for environment provisioning and service management.
- [x] **Distributed Inference**: Multi-node tensor pooling via llama-rpc.
- [x] **Task Graph Engine**: Persistent, SQLite-backed orchestration for complex agent goals.

### Security & Collaboration
- [x] **Hermetic Substrate**: Isolated execution environments via Docker and WASI.
- [x] **LAN Sovereignty**: Mandatory mTLS/SSL for all mesh traffic and secure device discovery.
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
- [x] **Plugin Hub & Local Marketplace**: Programmed dynamic Plugin Hub endpoints (`skills/marketplace` & `skills/publish`) with mock local persistence, duplicate prevention, and developer identity overrides.
- [x] **Unified Discovery Canvas**: Designed a glassmorphic marketplace UI catalog in the browser featuring installing loaders and neon green "INSTALLED" badges synced to active registries.
- [x] **Codebase Hygiene & Purges**: Removed spec legacy directories (`SubstrateDashboard`), audited voice synthetics fallback, and eradicated all linter, formatter, typecheck, and runtime warnings/errors.
- [x] **Sanitized Dual-Remote Git Sync**: Implemented worktree-free sanitized sync logic force-pushing snapshot tags to public GitHub mirror (`github`) while keeping full development history on internal Gitea (`origin`).

### Persistent Cognitive Substrates & LAN Mesh (v0.9.0)
- [x] **📡 Peer-to-Peer Mesh Sync**: Decentralized cross-device workspace syncing over LAN using secure TLS/mTLS without requiring central coordination.
- [x] **🧠 Swarm Memory Substrate (Hive Mind)**: Vector-backed memory engine storing structural architectural conventions, patterns, and past session contexts for local cognitive recall.
- [x] **🛡️ Secure Capability Guardrails**: Upgraded runtime sandbox granting granular, secure web searches and authenticated API capabilities with real-time human confirmation.

---

## 🛠️ Future Backlog

### Cognitive Refinement & Dynamic Autonomy
- [ ] **📈 Local Screenplay Teleplay Replay Canvas**: chronologically visualizing exact agent thought sequences during debug walkthroughs.
- [ ] **⚙️ Dynamic Autonomy Level Transition**: On-the-fly toggling of execution authority ceilings from full-trust manual bypass to strict verification loops.

---
*Roadmap updated to reflect Swarm Memory & Secure Capability Guardrails (v0.9.0).*
