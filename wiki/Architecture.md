# System Architecture

Neurex is designed as a **Supervised Swarm**. Unlike traditional IDEs, every action is a "Task" in a persistent, traceable graph.

## 1. The Orchestrator (Supervisor)
The Orchestrator is the brain of the system. It:
- Parses user intent into a `TaskGraph`.
- Delegates sub-tasks to specialized Agents (`coder`, `reviewer`, `infra`).
- **Context Summarization**: Condenses execution history automatically when tokens exceed the 4k threshold to maintain high-precision reasoning.

## 2. TaskGraph (The Ledger)
A SQLite-backed state machine tracking every agentic thought and tool call.
- **Statuses**: `pending` → `thinking` → `done`/`failed`.
- **HITL**: Human-in-the-Loop gating for high-stakes file operations.

## 3. Hive Mind (Memory)
A ChromaDB vector store that semantically indexes the entire workspace.
- **MemoryWorker**: A non-blocking background task that embeds code changes in real-time.
- **Context Retrieval**: Agents perform similarity searches to understand codebase patterns before writing new code.

## 4. The Mesh Hub
Handles decentralized communication between multiple Neurex nodes.
- **Load Balancing**: Routes LLM requests to nodes with the lowest VRAM utilization.
- **Protocol**: Zero-trust, encrypted WebSocket streams.
