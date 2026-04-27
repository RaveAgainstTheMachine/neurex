# Neurex System Architecture

Neurex is built as a distributed Master-Worker system composed of a centralized orchestration API and a federated mesh of inference nodes.

## 1. System Overview

### 1.1 Components
- **neurex-web**: A Vite/React frontend utilizing Monaco Editor for code editing and Xterm.js for terminal emulation.
- **neurex-api**: A FastAPI backend managing task graphs, agent orchestration, and node registration.
- **ChromaDB**: Vector database for semantic memory and codebase indexing.
- **llama-rpc-server**: Low-level distributed tensor pooling for cross-node inference.
- **MemoryWorker**: Background process for real-time filesystem indexing.

### 1.2 Data Flow: Distributed Inference
1.  **Request**: The `Orchestrator` requests a token completion.
2.  **Routing**: The `MeshRouter` evaluates node telemetry (VRAM, Latency, Queue).
3.  **Dispatch**: The request is sent to the selected `llama-rpc-server` instance.
4.  **Pooling**: If a model is split across nodes, the RPC layer synchronizes tensors across the network backplane.
5.  **Stream**: Tokens are streamed back to the `neurex-api` and broadcast via WebSocket to the frontend.

## 2. Agentic Framework & Task Graph

### 2.1 Task Graph (SQLite)
Neurex utilizes a persistent task graph to manage complex, multi-step engineering goals.
- **Schema**: Managed via SQLModel (SQLAlchemy).
- **Nodes**: Represent atomic actions (e.g., "Write test for auth.py").
- **State Machine**: Tasks transition through `PENDING` -> `THINKING` -> `EXECUTING` -> `COMPLETED/FAILED`.
- **Concurrency**: The graph allows for parallel task execution when dependencies are met.

### 2.2 Agent Personas
Agents inherit from a `BaseAgent` class providing RAG context, tool-calling loops, and logging.
- **Planner Agent**: Uses high-reasoning models to generate the initial task graph.
- **Coder Agent**: Focused on surgical codebase modifications using the `write_file` tool.
- **Reviewer Agent**: Performs validation using a "Critique-and-Refine" loop.

## 3. Hive Mind: Semantic Memory

### 3.1 Indexing Pipeline
- **Observation**: `watchdog` detects a `FileCreated` or `FileModified` event.
- **Parsing**: `Tree-Sitter` generates a Concrete Syntax Tree (CST) to identify logical code blocks.
- **Embedding**: Chunks are processed via `sentence-transformers` (e.g., `all-MiniLM-L6-v2`).
- **Upsert**: Vectors and metadata (file path, line range, node type) are stored in ChromaDB.

### 3.2 Retrieval (RAG)
Before every agent execution, the `MemoryWorker` performs a semantic search against the prompt. The top-$N$ results are injected into the agent's system prompt as "Project Context," reducing hallucination and providing architectural awareness.

## 9. Attributions & Citations

Neurex is built upon the foundational work of the global AI and Open Source research community. We gratefully acknowledge the following sources:

### 9.1 Model Weights & Architectures
- **Qwen2.5-Coder Series**: Alibaba Cloud / Qwen Team (Alibaba Group).
- **Llama 3 Series**: Meta AI (Meta Platforms, Inc.).
- **Whisper & Clip**: OpenAI.
- **Stable Diffusion XL**: Stability AI.

### 9.2 Performance Benchmarks
Static performance metrics (MMLU, HumanEval, etc.) utilized by the `LLMRecommender` system are sourced from:
- **Hugging Face Open LLM Leaderboard**: Managed by the Hugging Face H4 team.
- **Artificial Analysis**: Performance and quality metrics for frontier models (https://artificialanalysis.ai).
- **LMSYS Chatbot Arena**: Crowdsourced evaluation platform (https://chat.lmsys.org).

### 9.3 Infrastructure & Protocols
- **llama.cpp / llama-rpc-server**: Georgi Gerganov and the `llama.cpp` contributors.
- **MCP (Model Context Protocol)**: Anthropic PBC.
- **Tree-Sitter**: Max Brunsfeld and the Tree-Sitter community.

---
© 2026 Steven Frost. All rights reserved.

## 4. Real-Time Communication

### 4.1 WebSocket Protocol
The system uses a unified WebSocket for all real-time events:
- **Streaming**: Low-latency token delivery for chat and terminal.
- **Presence**: Synchronization of `user_id`, `cursor_position`, and `active_file`.
- **Infrastructure**: Real-time broadcast of node health and VRAM utilization.

### 4.2 PTY Persistence
The `PTYManager` decouples the shell process from the network socket.
- **Master Process**: A persistent Python process manages the pseudo-terminal.
- **Buffering**: Standard output is buffered in a ring buffer.
- **Reattachment**: If a user refreshes their browser, the frontend requests a reattach, and the buffer is replayed to restore state.

## 5. Security Model

### 5.1 Sandbox Isolation
Execution tools run inside a Docker container using the `neurex-sandbox` image.
- **Flags**: `--rm`, `--network none`, `--memory 512m`, `--cpus 1`.
- **Mounts**: The project directory is mounted as `:ro` (Read-Only).
- **Communication**: Results are captured via `stdout/stderr` and returned to the agent.

### 5.2 Authentication Logic
- **HS256 JWT**: Tokens contain `sub` (username) and `exp` (expiration).
- **Session Lifespan**: Hard-coded 8-hour expiry.
- **MFA Enforcement**: TOTP tokens are required for all non-GET requests to `/api/settings` and `/api/auth/admin`.
