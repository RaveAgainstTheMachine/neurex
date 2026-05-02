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

## 8. Neural Hardware Virtualization (Phase 47)
Phase 47 virtualizes the Mesh's physical substrate into a single, unified neural compute pool.
- **Virtual VRAM Pool**: Aggregates distributed VRAM across the Mesh for massive parallel reasoning.
- **Neural Swap-Space**: High-speed RAM/VRAM state swapping to bypass physical hardware limits.
- **Autonomous Re-Quantization**: Dynamic model precision shifting (e.g. Q8 -> IQ2) to maintain reasoning throughput under pressure.
## 9. Hermetic Substrate (Phase 53/54)
Phase 53/54 transitions the IDE from a manual development setup to a frictionless, zero-dependency native substrate.

### Dual-Layer Architecture
The system is logically split into two isolated planes to balance host performance with agent security:
- **Control Plane (Host Layer)**: A native Rust daemon (`neurex-cli`) that governs the substrate. It embeds the entire React frontend and serves it via an internal `axum` web server. It manages hardware diagnostics and life-cycle orchestration.
### Execution Plane (Triple-Tier Sandbox)
The system uses a resilient, multi-stage execution model to ensure agentic security and functional continuity across all platforms:
- **Tier 1: Performance (Docker)**: High-speed, native Linux containerization with full tool-chain support and hardware (NVIDIA/AMD) acceleration.
- **Tier 2: Portability (WASM/WASI)**: An architecture-agnostic sandbox powered by `wasmtime`. Ideal for zero-dependency execution and instant-on micro-tasks.
- **Tier 3: Reliability (Native Substrate)**: A jailed, pure-Rust filesystem executor built directly into the CLI. Acts as the ultimate safety net for basic operations when Docker/WASM are unavailable.

### Proactive Provisioning (Autonomous Onboarding)
Beyond hermetic runtimes, the daemon possesses a sentient environment setup engine (`neurex provision`):
- **Hardware-Aware Synthesis**: Detects specific GPU (Nvidia/AMD/Intel) and CPU (Apple Silicon/x86) architectures.
- **Interactive Authorization**: Suggests and executes platform-specific installation commands (apt, dnf, pacman, brew) to install Docker and hardware runtimes.
- **Cross-Platform Diagnostic**: Provides actionable diagnostic reports through `neurex doctor`, bridging the gap between a vanilla host and a high-performance neural compute node.

### Universal Mesh & Mobile Node Path
The Rust-first core enables the daemon to be cross-compiled for mobile platforms, allowing mobile NPUs (Snapdragon X, Apple A-Series) to participate as first-class compute nodes in the federated Neurex Mesh.

## 10. The Sentient UI (Phase 55)
Phase 55 bridges the gap between complex substrate logic and user-facing transparency through the **Substrate Dashboard**.

- **Real-Time Telemetry Bridge**: The Rust Control Plane exposes a persistent status API (`/api/substrate/status`) that streams hardware health and execution tier readiness to the frontend.
- **Visual Health Gating**: The dashboard uses animated, color-coded state transitions (Framer Motion) to confirm when the Performance (Docker) or Portability (WASM) tiers are active.
- **Hardware-Aware Visualization**: Detects and displays specific hardware traits (e.g., NVIDIA GPU Acceleration) directly in the UI, providing immediate confirmation of provisioning success.
- **Sentient Diagnostics**: Integrates the "Doctor" intelligence directly into the IDE sidebar, suggesting platform-specific fixes without requiring the user to return to the terminal.
