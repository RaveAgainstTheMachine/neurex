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

## 5. [[Language-Intelligence]] Hub
Provides native, plugin-free code intelligence for the IDE.
- **LSP Manager**: Automated discovery of system-installed language servers and "Autopilot" provisioning for 100+ languages.
- **Neural Lens Suite**: Renders real-time inline diagnostics (Error Lens) and authorship context (GitLens) using high-fidelity Monaco decorations.
- **Custom Intelligence**: Supports workspace-level overrides via `.neurex/lsp.json` for proprietary language support.
32. 
33. ## 6. Multi-Root Workspace
34. Enables enterprise-grade management of multiple project folders within a single session.
35. - **Root-Scoped Operations**: All file APIs are root-aware, using strict path resolution to prevent cross-project traversal.
36. - **Contextual PTY**: Integrated terminals are anchored to specific project roots. When spawning a shell, the system automatically detects the current file's root and sets the `cwd` (working directory) accordingly.
37. - **Dynamic Breadcrumbs**: Provides instant orientation by prefixing file paths with their workspace root name.
38. 
## 7. Sentient Mesh (Phase 45/46)
Phase 45/46 evolves the Hub into a self-regulating, architecture-aware substrate.
- **Neural Linter**: Every mutation is intercepted and verified against architectural standards before execution.
- **Swarm Consensus**: Critical architectural assets require a democratic quorum (3+ votes) from distinct agent personas.
- **Runtime Evolution**: The Mesh can hot-swap its own Python modules in-place via `LiveReloader`, enabling zero-restart logic updates.
- **Predictive Maintenance**: Proactively monitors codebase churn and triggers re-indexing to prevent context entropy.
