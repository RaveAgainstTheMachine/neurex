# Neurex System Architecture

Neurex is built as a distributed Master-Worker system composed of a centralized orchestration API and a federated mesh of inference nodes.

## 1. System Overview

### 1.1 Components
- **neurex-web**: A Vite/React frontend utilizing Monaco Editor for code editing and Xterm.js for terminal emulation.
- **neurex-api**: A FastAPI backend managing task graphs, agent orchestration, and node registration.
- **ChromaDB**: Vector database for semantic memory and codebase indexing.
- **llama-rpc-server**: Low-level distributed tensor pooling for cross-node inference.
- **MemoryWorker**: Background process for real-time filesystem indexing.
- **Multi-Root Workspace Engine**: A root-aware filesystem abstraction layer that enables parallel project management within a single IDE session.

### 1.2 Data Flow: Distributed Inference
1.  **Request**: The `Orchestrator` requests a token completion.
2.  **Routing**: The `MeshRouter` evaluates node telemetry (VRAM, Latency, Queue).
3.  **Dispatch**: The request is sent to the selected `llama-rpc-server` instance.
4.  **Pooling**: If a model is split across nodes, the RPC layer synchronizes tensors across the network backplane.
5.  **Stream**: Tokens are streamed back to the `neurex-api` and broadcast via WebSocket to the frontend.

### 1.3 Network & Port Governance
Neurex implements a dynamic, zero-trust network model:
- **Port Mapping**: All core services (API, Web, RPC, ChromaDB) have user-configurable ports persisted in the node registry.
- **Dynamic Firewall**: The `SettingsManager` automatically re-applies host-level firewall rules (using `iptables` or `ufw` abstractions) when ports or security toggles (LAN Isolation) are modified.
- **Zero-Trust Toggles**: Optional restriction of all Neurex traffic to the local network subnet (LAN-only mode) for high-security environments.

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

## 7. The Reasoning Economy

Neurex operates on a "Reasoning Economy" where intelligence is treated as a managed resource.

### 7.1 Iterative Loops vs. One-Shot
Unlike traditional IDE completions, Neurex utilizes **Iterative Reasoning Loops**. 
- **The Planning Phase**: High-context models (32B+) generate a DAG (Directed Acyclic Graph) of sub-tasks.
- **The Execution Phase**: Smaller, specialized models (7B/14B) execute atomic code changes.
- **The Verification Phase**: Agents perform self-critique using the `test_execution` tool in the sandbox.
- **Correction**: If a test fails, the graph is dynamically re-routed to a "Fix" node.

### 7.2 Resource Management
The "Agentic OS" treats compute (VRAM) and context (tokens) as finite assets:
- **Telemetry-Aware Dispatch**: The system monitors GPU temperatures and memory pressure on all Mesh nodes.
- **Dynamic Context Pruning**: RAG results are filtered by semantic density, ensuring the "Brain" (LLM) is not overloaded with noise.

## 8. Distributed Context (The Hive)

Neurex implements a **Decentralized Memory Model** that circumvents the limitations of fixed context windows.

### 8.1 Long-Term Semantic Recall
The Hive Mind isn't just for the current file; it's a project-wide vector space. 
- **Cross-Project Intelligence**: Agents can "recall" how a specific auth pattern was implemented in a sibling repository on the Mesh.
- **Context Pinning**: Users can manually "pin" historical fragments, forcing them into the agent's active reasoning cycle.

### 8.2 The Flight Recorder (Total Observability)
Transparency is the foundation of high-trust automation. The Flight Recorder provides:
- **Reasoning Traces**: Real-time streaming of the agent's "Internal Monologue."
- **Tool-Call Auditing**: Every file read, write, and shell command is logged and verifiable.
- **State Snapshots**: The ability to inspect the task graph at any point in time.

## 9. Attributions & Citations

Neurex is built upon the foundational work of the global AI and Open Source research community. We gratefully acknowledge the following sources:

### 9.1 Model Weights & Architectures (Open Source Policy)
Neurex adheres to a strict **Open Source Only** policy. We do not support or integrate with closed-source, paid API providers (OpenAI, Anthropic, etc.). We rely on the following elite open weights:
- **Qwen2.5-Coder Series**: Alibaba Cloud / Qwen Team (Alibaba Group).
- **Llama 3 Series**: Meta AI (Meta Platforms, Inc.).
- **Mistral & Mixtral**: Mistral AI.
- **DeepSeek Series**: DeepSeek AI.
- **Whisper**: OpenAI (Open Weights).

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

## 6. Federated Governance

### 6.1 Collaboration Manager (Distributed Locking)
To prevent mutation collisions in the federated mesh, Neurex implements a distributed locking system:
- **Lock Registry**: A DB-backed (SQLite) table `FileLock` tracks exclusive ownership of codebase assets.
- **Auto-Acquisition**: Agents automatically attempt to acquire a lock before executing `write` or `delete` tools.
- **Collision Handling**: If a file is locked by another node or user, the agent receives a `MUTATION_BLOCKED` response, ensuring atomic integrity.

### 6.2 Presence & Synchronization
Real-time state is synchronized across the mesh via WebSockets:
- **Presence Bar**: Displays active users and agent personas in the current session.
- **Visual Locking**: The File Explorer renders pulsing lock badges for files currently being mutated by the swarm.
- **Shared Scratchpad**: A collective in-memory buffer allowing agents to pass technical "gotchas" and findings to their swarm siblings.

## 11. Multi-Root Workspace Model

Neurex supports enterprise-grade multi-project management through a root-aware architecture.

### 11.1 Root-Scoped File Operations
All file system API endpoints are "root-aware." When a workspace contains multiple folders, operations (Read, Save, Search, Delete, Rename) include a `root_path` parameter. The backend validates paths against their specific project root using strict resolution checks, preventing cross-root traversal.

### 11.2 Contextual Terminal Management
Integrated terminals in Neurex are anchored to specific project contexts. 
- **Anchoring**: When a new terminal is spawned, it interrogates the IDE's active state to determine the current file's root.
- **PTY Spawning**: The `PTYManager` initializes the shell process with the identified `cwd` (current working directory), ensuring that `git` commands and build scripts run in the correct project environment.

### 11.3 State Synchronization & UI Context
The frontend `NeurexStore` tracks the source root for every asset:
- **Tabs**: Editor tabs use `${root}:${path}` identifiers to support duplicate filenames across different projects.
- **Navigation**: Breadcrumbs are prefixed with the workspace root name to provide instant spatial orientation.
- **Presence**: User and agent presence are scoped to the active project root, allowing for focused collaboration.
## 10. Language Intelligence & LSP Hub

Neurex implements a high-performance, native LSP Hub that provides IDE-grade intelligence without the overhead of external plugins.

### 10.1 Backend LSP Manager
The `LSPManager` orchestrates language server subprocesses on the host machine.
- **Discovery**: Scans the system `PATH` and `.neurex/bin/lsp` for known binaries.
- **Dynamic Fallback**: If a language is unrecognized, the manager interrogates the system for standard patterns (e.g., `lang-lsp`, `langls`) to provide zero-config intelligence for niche languages.
- **Custom Configuration**: Supports workspace-level overrides via `.neurex/lsp.json`, allowing developers to define proprietary LSP commands.
- **Lifecycle**: Manages the startup, health checks, and shutdown of server instances.
- **Bridging**: Transparently pipes standard I/O from the LSP subprocess to a dedicated WebSocket endpoint.

### 10.2 Neural Lens & Decorations
The frontend implements a high-fidelity visual layer atop the LSP data:
- **Neural Error Lens**: Groups diagnostic markers (Errors, Warnings) and renders them inline directly following the relevant code lines.
- **Neural GitLens**: Interrogates the Git subsystem to provide real-time commit blame and file history, rendered as "ghost text" decorations.
- **Formatting Engine**: Intercepts save operations to trigger the LSP's formatting capability, ensuring codebase consistency.

### 10.3 Communication
- **Protocol**: Standard JSON-RPC 2.0 over WebSockets.
- **Multiplexing**: While chat and telemetry share a socket, LSP traffic utilizes dedicated per-language channels to ensure zero-latency intelligence during heavy agent execution.
## 12. Performance & Throughput Scaling

Neurex is engineered for "High-Frequency Intelligence," where the UI must remain fluid during massive background swarm activity.

### 12.1 UI State Management (Strict Selectors)
The frontend utilizes a "Strict State Subscription" pattern to prevent global re-render churn.
- **Granular Selectors**: Components MUST use discrete Zustand selectors (`useStore(s => s.property)`) rather than subscribing to the entire store object.
- **Architectural Decoupling**: The root `App` component and major panels are decoupled from high-frequency state (cursor tracking, diagnostics, telemetry) to ensure the global layout remains static and responsive.
- **O(1) Operations**: Large-scale UI interactions (e.g., file explorer status updates) are optimized for constant-time complexity, utilizing shallow lookups rather than recursive tree traversals.

### 12.2 WebSocket Throughput (Aggressive Buffering)
To prevent network saturation and UI thread starvation, Neurex implements a dual-layer buffering strategy:
- **Backend Token Chunking**: LLM tokens are aggregated into blocks of 10 on the server before being broadcast, reducing message frequency by ~90%.
- **Frontend Streaming Buffer**: The WebSocket hook implements a 40ms (25fps) micro-buffer for incoming tokens, aggregating them into a single store update per frame. This ensures smooth text rendering without saturating the React reconciliation engine.

### 12.3 High-Throughput Observability
The `FlightRecorder` and `SystemLogs` utilize a non-blocking, buffered I/O model:
- **Batch-Writing**: Observability traces are written to a background ring buffer and flushed to the database in 2-second intervals.
- **Memoized Rendering**: Reasoning traces and task updates are rendered using memoized components (`React.memo`), ensuring that only the new fragments of the trace incur a DOM cost.

### 12.4 Accelerated Backend I/O
- **Fast Serialization**: The API utilizes `orjson` as its primary serialization engine, significantly reducing the CPU cost of generating large JSON responses for telemetry and file tree operations.
- **Connection Pooling**: All Mesh-wide service calls (RAG, Memory, Agents) are performed via persistent `httpx.AsyncClient` pools to eliminate the overhead of TCP/TLS connection churn.
## 13. Sentient IDE: Autonomous Self-Regulation
 
Phase 45 transforms Neurex from an assistive tool into a self-governing, self-healing agentic mesh capable of autonomous architectural oversight.
 
### 13.1 Neural Linter (Architectural Middleware)
The `NeuralLinter` serves as an intelligent gatekeeper within the `BaseAgent` tool dispatch pipeline.
- **Validation Loop**: Every filesystem mutation is interrogated by a high-reasoning model against `ARCHITECTURE.md` and `DESIGN_SYSTEM.md` before execution.
- **Feedback & Correction**: If a mutation is rejected, the linter returns a detailed architectural rationale, triggering an **Autonomous Self-Repair Loop** where the agent reflects on the failure and regenerates a compliant change.
 
### 13.2 Swarm Consensus Protocol
Critical architectural assets (core agent logic, infrastructure, task graphs) are protected by a democratic governance layer.
- **Consensus Manager**: Tracks mutation proposals for protected paths.
- **Voting Threshold**: Mutations to core assets require a minimum of 3 positive votes from distinct agent personas (e.g., Coder, Reviewer, Planner).
- **Consensus Evaluation**: Specialized reviewer agents are autonomously spawned to evaluate and vote on proposals, preventing unilateral "Neural Drift."
 
### 13.3 Runtime Evolution (Zero-Restart)
The `LiveReloader` service enables the Mesh to update its own core logic without terminating the process.
- **Module Hot-Swapping**: Utilizes in-place module reloading to inject new agent behaviors or infrastructure fixes directly into the running process.
- **Instant Adoption**: Evolution is immediate; once a consensus-backed mutation is written, the system adopts the new logic for all subsequent tasks.
 
### 13.4 Predictive Maintenance
The IDE proactively manages its own intelligence state to ensure long-term stability and reliability.
- **Churn Heuristics**: The `MaintenanceService` monitors filesystem events from the `Watcher`. When codebase churn exceeds a defined threshold, it triggers a background workspace re-indexing.
- **Stale Index Detection**: Periodically refreshes RAG and Memory pointers to ensure the agentic context remains synchronized with the physical reality of the codebase.

## 14. Neural Mesh Integration (Phase 46)
Phase 46 evolves the Mesh into a coherent, unified neural substrate where compute and context are pooled across federated nodes.

### 14.1 Attention Pooling (Distributed Reasoning)
The `AttentionCoordinator` orchestrates federated reasoning by distributing specific attention heads across Mesh nodes.
- **Federated Parallelism**: Enables sub-ms parallelization of model mechanisms, effectively pooling the collective intelligence of all available nodes into a single 'Virtual Super-Brain'.

### 14.2 Global Context Sharding (KV-Cache Federation)
Massive context windows (128k+ tokens) are sharded across the Mesh to circumvent individual VRAM limitations.
- **Context Sharding**: The `ContextSharder` slices the input space into federated segments, each managed by a distinct node's K/V cache.
- **Unified Memory**: Allows high-reasoning tasks on massive repositories without requiring high-VRAM 'Whale' nodes.

### 14.3 Predictive Neural Prefetching
The `NeuralPrefetcher` eliminates cold-start latency by priming nodes based on agent trajectory.
- **Trajectory Analysis**: Inspects upcoming swarm plans to pre-emptively load model weights and specific neural contexts into VRAM.

### 14.4 Sub-ms Mesh Backplane (KV-Sync)
The `KVSyncProtocol` ensures neural coherence during distributed sessions.
- **State Propagation**: Synchronizes hidden state deltas and K/V cache updates between nodes with targeted sub-5ms latency, ensuring architectural consistency across the federated substrate.

## 15. Neural Hardware Virtualization (Phase 47)
Phase 47 virtualizes the Mesh's physical substrate into a single, unified neural compute pool.

### 15.1 Virtual VRAM Pooling (Mesh Aggregation)
The `VirtualVRAMPool` aggregates the VRAM of all online peers into a single virtual pool.
- **Resource Sharding**: Orchestrates massive models and context shards across multiple nodes, circumventing individual hardware limitations.

### 15.2 Neural Swap-Space (RAM/VRAM Hybridization)
The `NeuralSwapManager` implements a high-speed state manager for swapping neural data between System RAM and VRAM.
- **PCIe Paging**: Enables "Virtual VRAM" expansion by offloading inactive layers/context to host memory during inference bursts.

### 15.3 Autonomous Re-Quantization (Dynamic Precision)
The `AutonomousQuantizer` dynamically shifts model precision based on Mesh resource pressure.
- **Graceful Degradation**: Automatically re-quantizes models (e.g., from Q8 to IQ2) to maintain reasoning throughput when VRAM utilization reaches critical thresholds.

### 15.4 Hardware Orchestrator (Mesh Resource Coordination)
The `HardwareOrchestrator` acts as the central intelligence for Mesh resource allocation.
- **Multi-Stage Fallback**: Coordinates pooling, swapping, and re-quantization to ensure that swarm tasks are successfully fulfilled regardless of local hardware constraints.

## 16. Neural Evolution (Phase 48)
Phase 48 enables the Mesh to autonomously optimize its own intelligence.

### 16.1 Evolution Coordinator
The `EvolutionCoordinator` manages the lifecycle of neural adapters (LoRA).
- **Success Telemetry**: Aggregates mission outcomes to trigger autonomous fine-tuning bursts.

### 16.2 Architecture Mutation
The `ArchitectureMutator` autonomously redesigns neural adapter structures.
- **Rank Resizing**: Dynamically increases LoRA rank or expands target modules based on task complexity.

## 17. Neural Collective Intelligence (Phase 49)
Phase 49 enables secure, cross-project knowledge sharing.

### 17.1 Project Distiller
The `ProjectDistiller` extracts 'Neural Lessons' (abstracted patterns) from evolved adapters.
- **Privacy Preservation**: Differential Privacy (DP) ensures that raw code is never exposed during knowledge transfer.

### 17.2 Swarm Knowledge Base
The `SwarmKnowledgeBase` maintains a decentralized index of global engineering best practices.
- **Collective Wisdom**: Agents inject distilled patterns into their system prompts for zero-shot performance gains.

## 18. The Sentient Singularity (Phase 50)
Phase 50 establishes the Mesh as a self-directed, self-improving entity.

### 18.1 Autonomous Goal Setting
The `GoalGenerator` autonomously analyzes Mesh entropy and proposes strategic engineering missions.
- **Self-Directed Evolution**: The system decides its own refactoring priorities.

### 18.2 Self-Generating Plugins
The `SelfPluginGenerator` autonomously authors and installs new IDE logic modules.
- **Capability Expansion**: The Mesh can program its own soul to solve mission-specific requirements.

## 19. Neural Self-Synthesis (Phase 51)
Phase 51 enables the Mesh to autonomously expand its codebase and optimize its core logic.

### 19.1 Project Inceptor
The `ProjectInceptor` enables the Mesh to autonomously spawn sub-projects and microservices.
- **Self-Expansion**: The system can physically scale its architecture by creating new specialized workspaces as needed.

### 19.2 Recursive Self-Optimizer
The `SelfOptimizer` autonomously refactors the Mesh's own core infrastructure source code.
- **Recursive Improvement**: Analyzes performance telemetry to rewrite its own soul for peak efficiency.
