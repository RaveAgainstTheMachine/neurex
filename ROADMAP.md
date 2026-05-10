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

## ⚡ Active Development: The Maintenance Pivot (v0.6.0)

Our current focus is transforming Neurex from a "general substrate" into a high-reliability **Autonomous Maintenance Engine**.

### 🛠️ Core Maintenance Workflows
- [ ] **Automated Dependency Hardening**: Tools for agents to upgrade library major versions and autonomously fix breaking changes.
- [ ] **Security Sentinel**: Background scanning and auto-patching of subprocess command injections and path traversals.
- [ ] **Type-Safety Enforcement**: Repo-wide autonomous addition of type hints and docstrings with verification.

### 🧪 Reliability & Evals
- [ ] **Release Evals**: Every release must pass a standardized suite of 50+ maintenance tasks (see `eval/run_evals.py`).
- [ ] **Agent Trace Debugger**: A high-fidelity UI for inspecting agent tool usage to reduce "loop hallucinations."
- [ ] **Regression Snapshots**: Automatic git snapshots before any agent mutation to ensure 100% rollback reliability.

### 🔬 Experimental Labs (Lower Priority)
- **Distributed VRAM Pooling**: Functional but considered a niche power-user feature.
- **Mobile Peer Support**: Experimental nodes for running inference on mobile NPUs.

---

## 🛠️ Future Backlog
- [ ] **Plugin System**: Public API for extending the IDE.
- [ ] **Multi-Agent Debate**: Refinement loop for high-risk maintenance tasks.

---
*Roadmap updated to reflect the Maintenance & Reliability pivot.*
