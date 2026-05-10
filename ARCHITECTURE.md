# Neurex System Architecture

Neurex is a local-first engineering workspace built as a distributed Master-Worker system. It composed of a centralized orchestration API and a federated mesh of inference nodes.

## 1. System Overview

### 1.1 Core Components
- **neurex-web**: A Vite/React frontend utilizing Monaco Editor for code editing and Xterm.js for terminal emulation.
- **neurex-api**: A FastAPI backend managing task graphs, agent orchestration, and node registration.
- **neurex-cli**: A native Rust control plane that manages the lifecycle of the API and Web services, including hermetic environment provisioning.
- **ChromaDB**: Vector database for semantic memory and codebase indexing.
- **llama-rpc-server**: Low-level distributed tensor pooling for cross-node inference (via llama.cpp).

### 1.2 Data Flow: Distributed Inference
1.  **Request**: The `Orchestrator` requests a token completion.
2.  **Routing**: The `MeshRouter` evaluates node telemetry (VRAM, Latency, Queue).
3.  **Dispatch**: The request is sent to the selected `llama-rpc-server` instance.
4.  **Pooling**: If a model is split across nodes, the RPC layer synchronizes tensors across the network backplane.
5.  **Stream**: Tokens are streamed back to the `neurex-api` and broadcast via WebSocket to the frontend.

## 2. Agentic Framework & Task Graph

### 2.1 Task Graph (SQLite)
Neurex utilizes a persistent task graph to manage complex, multi-step engineering goals.
- **Nodes**: Represent atomic actions (e.g., "Write test for auth.py").
- **State Machine**: Tasks transition through `PENDING` -> `THINKING` -> `EXECUTING` -> `COMPLETED/FAILED`.
- **Concurrency**: The graph allows for parallel task execution when dependencies are met.

### 2.2 Agent Personas
Agents inherit from a `BaseAgent` class providing RAG context, tool-calling loops, and logging.
- **Planner Agent**: Generates the initial task graph.
- **Coder Agent**: Performs codebase modifications using filesystem tools.
- **Reviewer Agent**: Validates changes using a "Critique-and-Refine" loop.

### 2.3 Dynamic Model Routing
- **Cognitive Roles**: Defined roles (e.g., Planning, Coding, Reviewing) act as abstract targets.
- **Dynamic Resolution**: The `Orchestrator` resolves the target model at runtime by consulting the `model_routes` registry.
- **User Governance**: Swapping models for specific roles in the UI without impacting underlying logic.

## 3. Memory & Retrieval (RAG)

### 3.1 Indexing Pipeline
- **Observation**: Detects filesystem events.
- **Parsing**: `Tree-Sitter` identifies logical code blocks.
- **Embedding**: Chunks are processed via local embedding models.
- **Upsert**: Vectors and metadata are stored in ChromaDB.

### 3.2 Retrieval
Before agent execution, the system performs a semantic search against the prompt. Top results are injected into the agent's context as "Project Context."

## 4. Real-Time Communication & PTY

### 4.1 WebSocket Protocol
A unified WebSocket handles all real-time events:
- **Streaming**: Token delivery for chat and terminal.
- **Presence**: Synchronization of cursor positions and active files.
- **Telemetry**: Real-time broadcast of node health and VRAM.

### 4.2 PTY Persistence
The `PTYManager` decouples the shell process from the network socket. Standard output is buffered, allowing users to reattach to terminals across sessions or page refreshes.

## 5. Security Model

### 5.1 Sandbox Isolation
Execution tools run inside a Docker container (`neurex-sandbox`).
- **Isolation**: Limited networking, memory, and CPU.
- **Mounts**: Project directory is mounted with restricted permissions.

### 5.2 Authentication & Encryption
- **JWT**: Token-based authentication for API access.
- **mTLS/SSL**: Enforced encryption for all non-loopback mesh traffic.
- **MFA**: Required for administrative setting changes.

## 6. Federated Governance & Locking

### 6.1 Distributed Locking
To prevent mutation collisions, a DB-backed registry tracks exclusive ownership of codebase assets. Agents acquire locks before executing write operations.

### 6.2 Presence Synchronization
Real-time state (active users, agent cursors) is synchronized via WebSockets to provide a collaborative "multiplayer" engineering experience.

## 7. Multi-Root Workspace Model
Neurex supports managing multiple projects simultaneously through a root-aware filesystem abstraction. API endpoints and terminals are scoped to specific project roots, preventing cross-project path traversal.

## 8. Language Intelligence (LSP Hub)
A native LSP Hub orchestrates language server subprocesses on the host. It provides diagnostics (Neural Lens), formatting, and symbol navigation via standard JSON-RPC over WebSockets.

## 9. Performance & Scaling

### 9.1 UI Optimization
- **Strict Selectors**: Components subscribe to discrete state fragments to prevent unnecessary re-renders.
- **Token Chunking**: LLM tokens are aggregated on the server before broadcast to reduce message frequency.

### 9.2 Backend Throughput
- **Fast Serialization**: Uses `orjson` for low-latency JSON generation.
- **Connection Pooling**: Persistent async client pools for mesh-wide service calls.

## 10. Hermetic Substrate (neurex-cli)
The Rust-based `neurex-cli` provides a zero-dependency entry point for Windows, macOS, and Linux. It autonomously provisions its own isolated Python environment (via `uv`) and manages the lifecycle of the entire mesh.

## 11. Secure LAN Sovereignty
The system implements mandatory SSL/TLS for LAN traffic, utilizes transparent proxies for identity propagation across nodes, and employs dynamic CORS whitelisting to secure multi-device collaboration.

## 12. Attributions & Citations
Neurex is built upon the foundational work of the global AI and Open Source research community, including `llama.cpp`, `Tree-Sitter`, `FastAPI`, `React`, and various open-weight model architectures (Qwen, Llama, Mistral).

---
© 2026 Neurex Collective. All rights reserved.
