# Neurex Technical Features

Neurex is a distributed, agentic integrated development environment (IDE) optimized for local-first software engineering. The system leverages consumer-grade hardware to execute large-scale open-source models through a federated compute mesh.

## 1. Distributed Inference & Resource Management
*   **VRAM Aggregation**: Utilizes `llama-rpc-server` to pool VRAM across multiple physical nodes. This enables the execution of large parameter models (e.g., Llama-3-70B+) that exceed the capacity of a single consumer GPU.
*   **MeshRouter Engine**: A dynamic load-balancing system that calculates node suitability scores based on:
    *   Available VRAM and System RAM.
    *   CPU pressure and thermal headroom.
    *   Real-time network latency (heartbeat telemetry).
    *   Current task queue depth.
*   **Automatic Peer Discovery**: Nodes broadcast capabilities every 15 seconds via a UDP/WebSocket heartbeat agent, allowing the Master node to maintain an up-to-date registry of the compute mesh.

## 2. Multi-Agent Orchestration
*   **Specialized Agent Personas**:
    *   **Planner**: Decomposes natural language objectives into a state-persistent SQLite task graph.
    *   **Coder**: Implements code changes using file-system tools (full-file rewrites for validation integrity).
    *   **Reviewer**: Performs static analysis and security auditing on proposed changes.
    *   **Tester**: Generates and executes test suites (`pytest`, `vitest`) within isolated containers.
    *   **Commander**: Executive supervisor that re-evaluates stalled plans and rewrites the task graph mid-execution.
*   **State Persistence**: All agent progress is tracked in a relational database, allowing for task resumption after system restarts or network interruptions.
*   **Iteration Governance**: Enforces staleness detection and iteration caps to prevent infinite tool-call loops.

## 3. Hive Mind (Collective Memory)
*   **Vector Knowledge Base**: Integrates **ChromaDB** for semantic indexing of the entire workspace.
*   **Code-Aware Chunking**: Uses **Tree-Sitter** to parse source files into logical chunks (functions, classes, blocks), preserving semantic context for retrieval.
*   **Asynchronous Indexing**: A dedicated `MemoryWorker` utilizes `watchdog` to re-index modified files in the background with < 150ms latency.
*   **Semantic Recall**: Agents utilize RAG (Retrieval-Augmented Generation) to inject relevant code patterns and architectural precedents into their context window.

## 4. Security & Sandbox Execution
*   **Docker Sandbox**: All terminal commands and test executions occur in isolated containers with:
    *   **No Network Access**: Standard configuration blocks all external traffic from the sandbox.
    *   **Read-Only Mounts**: The workspace is mounted as RO to prevent agents from modifying files via shell (enforced surgical write tools only).
    *   **Resource Capping**: Hard limits on memory (512MB) and CPU (1 vCPU) per execution.
*   **Human-in-the-Loop (HITL)**: Commands exceeding the configured autonomy ceiling require manual sign-off via the Master or Mobile interface.
*   **Authentication & RBAC**:
    *   **JWT Security**: HS256 signed tokens with mandatory 8-hour rotation.
    *   **Credential Hashing**: PBKDF2-SHA256 with 600k iterations.
    *   **MFA**: Mandatory TOTP for administrative actions and remote approvals.

## 5. Real-Time Collaboration & Interface
*   **Persistent PTY Manager**: Manages shell sessions through a detach/attach lifecycle, allowing terminal state to persist across browser refreshes and client handoffs.
*   **WebSocket Presence**: Synchronizes cursor positions, active file locks, and agent statuses across all connected clients in real-time.
*   **Dynamic API Resolution**: Automatically derives API and WebSocket endpoints from the origin URL, enabling seamless multi-device access (Desktop/Mobile) without configuration changes.
*   **Mobile Web Interface**: A PWA-optimized control center for monitoring mesh telemetry and issuing remote task approvals.
*   **Graph Cancellation**: Reactive 'Panic Button' capability to immediately halt complex multi-agent workflows.

## 6. The Forge: Workspace Integrity
*   **Deep Cleaning**: Automated purging of environment debris (`__pycache__`, caches) and `git` pruning.
*   **Auto-Linting**: Integrated `ruff --fix` for instantaneous code hygiene.
*   **Project Intelligence**: Autonomous synthesis of an architectural 'brain' (`intel.json`) by parsing documentation and source code.
*   **Self-Onboarding**: The Planner automatically force-injects architectural discovery steps for new or un-profiled workspaces.

## 7. The Sentinel: Security Auditing
*   **Static Analysis**: Integrated `bandit` scanning for Python security vulnerabilities.
*   **Vulnerability Tracking**: `safety` check for known exploits in the dependency tree.
*   **Leak Detection**: Automated scanning of the Git index for accidental secret leaks (`.env`, `.pem`).

## 8. The Immune System: Self-Healing Loops
*   **Iterative Debugging**: The Orchestrator automatically detects test failures and re-activates preceding coding tasks with failure logs as context.
*   **Quality Gates**: Multi-pass architectural review and testing cycles (up to 10 iterations) to ensure structural integrity without human intervention.
*   **Mesh Awareness**: Agents can query `get_mesh_topology` to understand the distributed health and performance of the federated swarm.
*   **Semantic RAG**: Conceptual indexing of codebases via a background summarization pass, enabling high-level architectural search.

## 9. Swarm Governance: The Commander
*   **Dynamic Graph Rewriting**: Mid-execution re-evaluation of stalled plans. The Commander autonomously cancels failed paths and appends new strategies to the task graph.
*   **Executive Oversight**: Global status monitoring across all agents to detect logical contradictions or technical blockers.
*   **Autonomous Strategy Pivoting**: Reactive architectural shifting when an agent hits its iteration limit without success.

## 10. Safety Lifecycle: Autonomous Self-Preservation
*   **Point-in-Time Snapshots**: Automated backups of the database, configuration, and architectural 'brain' before every system update.
*   **One-Click Rollback**: Robust recovery path to restore the IDE to a known-stable state if an update fails or state is corrupted.
*   **Operational Transparency**: Visual tracking of system snapshots directly within the Update Notifier dashboard.

## 10. Infrastructure Lifecycle
*   **Automated Self-Updates**: Background release monitoring with integrated `docker compose` pull triggers for background versioning.
*   **Role-Aware Installer**: A unified bootstrap script that detects environment capabilities and configures the node as either a Master or an RPC Worker.
*   **Observability**: Integrated structured logging (`structlog`) for deep-trace debugging across the entire distributed stack.
