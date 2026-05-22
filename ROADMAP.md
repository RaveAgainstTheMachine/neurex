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

## ⚡ Active Development: The Interactive Agentic Pivot (v0.6.0)

Our current focus is elevating Neurex from a background task sandbox into a premier, high-fidelity **Interactive Agentic IDE** where developers and AI agents collaborate visually as true equal peers.

### 🎨 Core Interactive IDE Workflows
- [ ] **Visual Agent Task Graph Editor**: A node-based designer canvas where users can visually rewire task dependencies, insert manual/agent steps, and set active execution breakpoints.
- [ ] **Multi-Cursor AI Pair Programming**: Real-time collaborative typing in Monaco with visual AI cursors (`[Neurex Coder]`), selection highlights, and 60Hz telemetry sync.
- [ ] **Bidirectional LSP Context Router**: Exposing language server operations (`find references`, `go to definition`, `diagnostics`) directly to agents to query semantic codebase relations.
- [ ] **Visual MCP Tool Sandbox & Manager**: A dashboard listing connected Model Context Protocol servers with a granular permission matrix (Always Allow, Always Ask, Deny) and manual tool playgrounds.

### 🧪 Reliability, Evals & Controls
- [ ] **Interactive Simulation Benchmarks**: Real-time evaluation runs designed to test agent responsiveness and cooperation in live visual environments.
- [ ] **Telemetry Replay Canvas**: An interactive debugger to record, play back, and inspect agent WebSocket events, PTY streams, and cursor selections.
- [ ] **Zero-Diff Staging Guard**: Sandboxed environment checking before committing swarm mutations, ensuring 100% stable workspace rollbacks.

### 🔬 Experimental Labs (Lower Priority)
- **Distributed VRAM Pooling**: Functional but considered a niche power-user feature.
- **Mobile NPU Nodes**: Experimental nodes for offloading inference to mobile devices.

---

## 🛠️ Future Backlog
- [ ] **Extensible Plugin Hub**: A community-driven marketplace for publishing and sharing custom agent toolkits and themes.
- [ ] **Multi-Agent Consensus Debates**: Automated high-stakes architecture reviews with multi-agent consensus voting.

---
*Roadmap updated to reflect the Interactive Agentic Pivot.*
