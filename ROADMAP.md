# Neurex Development Roadmap

This document outlines the development trajectory of Neurex, focusing on building a stable, local-first AI engineering workspace.

## 🛰️ Current Operational Status
- **Current Version**: `v0.5.3-STABLE`
- **Core Engine**: NeuralHarness v2.1
- **Status**: Stable for local and LAN-based multi-device collaboration.

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

---

## ⚡ Active Development (v0.6.0 Horizon)

### Substrate Optimization
- [ ] **Inference Caching**: Aggressive caching of prompt prefixes to reduce GPU overhead during iterative tasks.
- [ ] **WASM Toolchain**: Self-generating WASI tools for zero-dependency agent operations on systems without Docker.
- [ ] **Binary Size Reduction**: Optimizing the Rust control plane for faster cold starts.

### Agent Capabilities
- [ ] **Improved Tool Reasoning**: Refining agent loops to handle large-scale refactors (>50 files) more reliably.
- [ ] **Context Pre-computation**: Background indexing of AST symbols during idle time.

---

## 🛠️ Future Backlog
- [ ] **Multi-Agent Collaboration**: Framework for multiple specialized agents to debate and review changes before surfacing to the human.
- [ ] **Plugin System**: Public API for extending the IDE with custom themes and language support.
- [ ] **Mobile Integration**: Leveraging on-device NPUs for RAG indexing on tablets and phones.

---
*Roadmap updated for the v0.5.3-STABLE release.*
