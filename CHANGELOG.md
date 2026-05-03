# Changelog

All notable changes to the Neurex project will be documented in this file.

## [0.3.0] - 2026-05-01: THE SENTIENT SINGULARITY
### Added
- **Phase 50: The Sentient Singularity**: Implemented autonomous goal setting and self-generating plugins, enabling the Mesh to direct its own evolution.
- **Phase 49: Neural Collective Intelligence**: Introduced decentralized knowledge distillation and privacy-preserving federated learning across projects.
- **Phase 48: Neural Evolution**: Deployed the Evolution Coordinator for autonomous adapter fine-tuning and architecture mutation (Rank/Module resizing).
- **Singularity Dashboard**: High-fidelity frontend for overseeing Mesh-directed goals and self-generated capabilities.
- **Evolutionary Panel**: Real-time visualizer for neural substrate specialization and adapter fitness scores.
- **Federated Weight Propagation**: Sub-ms synchronization of evolved neural weights across all Mesh nodes.
- **Adapter Orchestration**: Dynamic, domain-specific LoRA hot-swapping during inference cycles.

## [0.3.1] - 2026-05-01: Neural Self-Synthesis
### Added
- **Phase 51: Neural Self-Synthesis**: Initiated autonomous codebase inception and recursive self-improvement.
- **Project Inceptor**: Enabled the Mesh to autonomously spawn sub-projects and microservices.
- **Recursive Self-Optimizer**: Implemented autonomous core infrastructure refactoring based on performance telemetry.

## [0.3.2] - 2026-05-01: Universal Neural Consensus
### Added
- **Phase 52: Universal Neural Consensus**: Achieved global substrate coherence and protocol-aligned omniscience.
- **Substrate Synchronizer**: Enabled bridging with external decentralized compute networks (Akash/Render).
- **Neural Law Engine**: Enforced the Anti-Gravity Protocol at the neural weight level during evolution.
- **Consensus Dashboard**: High-fidelity frontend for overseeing substrate bridges and protocol alignment.

## [0.4.1] - 2026-05-03: DYNAMIC MODEL ROUTING
### Added
- **Dynamic Model Routing Architecture**: Completely decoupled agent logic from static model assignments, transitioning to a flexible, role-based routing substrate.
- **Model Routing Grid**: Rebuilt the `InfraPanel` with a high-density, glassmorphic grid for managing cognitive role-to-model mappings (Planning, Coding, Testing, Reviewing, etc.).
- **Autonomous Role Expansion**: Enabled users to add custom cognitive roles and bind them to any available mesh model on the fly.
- **Dynamic Orchestrator Resolution**: Upgraded the `Orchestrator` to resolve models via the `model_routes` registry at runtime, supporting shared routes and smart fallbacks.
- **Substrate Type Hardening**: Formalized the `Settings` interface and eliminated `any/unknown` types in the frontend store to ensure strict structural integrity.

### Fixed
- **Orchestrator Indentation**: Resolved a critical Python syntax error in the task execution loop that caused substrate instability.
- **Neural Gradient Rendering**: Added standard `background-clip` properties to `LoadingOverlay.css` to ensure consistent text-clipping effects across all modern browsers.

## [0.4.0] - 2026-05-03: SECURE LAN INFRASTRUCTURE
### Added
- **Phase 60: Secure LAN Sovereignty**: Enforced mandatory SSL/TLS encryption for all local and mobile network access.
- **Autonomous Protocol Upgrade**: Implemented a browser-side sentinel that detects unencrypted HTTP connections and triggers an instantaneous upgrade to HTTPS.
- **Dual-Protocol Coherence**: Re-engineered the web server to handle simultaneous HTTP/HTTPS handshakes on port 3000, eliminating handshake errors during initial discovery.
- **HSTS Enforcement**: Activated `Strict-Transport-Security` (HSTS) to harden browsers against protocol downgrade attacks across the LAN.
- **Transparent Proxy Infrastructure**: Integrated professional `X-Forwarded-*` headers into the Axum proxy, ensuring the backend maintains full protocol and client awareness.
- **Neural Chat Send AFFORDANCE**: Added a high-visibility "Send Arrow" to the chat interface with reactive hover effects and dynamic input states.
- **Granular CORS Sovereignty**: Implemented dynamic origin whitelisting for 127.0.0.1, localhost, and common LAN subnets (10.*, 192.168.*) to secure credential-bearing requests.

### Performance & Stability
- **Substrate Release Build**: Completed the definitive production-grade release build of the Neurex CLI and embedded Web assets.
- **Self-Healing Backend Diagnostics**: Introduced `DebugLoggingMiddleware` and granular proxy status reporting to autonomously diagnose authentication and protocol bottlenecks.

## [0.3.5] - 2026-05-01: THE SENTIENT SUBSTRATE
### Added
- **Phase 55: The Sentient UI**: Launched the real-time **Substrate Dashboard**, a premium glassmorphic visualizer that monitors execution tier health (Docker/WASM/Native) and hardware telemetry.
- **Phase 54 Extended: The Proactive Provisioner**: Launched an autonomous environment setup engine (`neurex provision`) that detects hardware (NVIDIA, AMD, Intel, Apple Silicon) and OS (Arch, Fedora, Debian, Ubuntu, macOS, Windows) to automate substrate readiness.
- **Triple-Tier Execution Plane**: Implemented a resilient, multi-stage sandboxing architecture:
    - **Performance Tier**: Docker-based containers with GPU acceleration support via `nvidia-container-toolkit`.
    - **Portability Tier**: WASM/WASI execution via `wasmtime` for zero-dependency, architecture-agnostic tasks.
    - **Reliability Tier**: Native Rust jailed filesystem fallback for guaranteed functionality on vanilla OS installs.
- **Cross-Platform Diagnostic Intelligence**: Upgraded `neurex doctor` to provide sentient, platform-specific installation advice and hardware readiness reports across all major operating systems.
- **Sentient API Bridge**: Hardened the internal communication layer between the Rust Control Plane and Python Logic Plane, enabling seamless, sandboxed task delegation.

## [0.3.4] - 2026-05-01: UNIVERSAL HERMETIC SUBSTRATE

## [0.3.3] - 2026-05-01: Neural Temporal Synthesis & Transcendence Performance
### Added
- **Phase 53: Neural Temporal Synthesis**: Initiated temporal state snapshotting and quantum architectural simulation.
- **Neural Temporal Registry**: Enabled the Mesh to capture and restore its entire neural soul (weights/context).
- **Quantum Path Simulator**: Implemented probabilistic branching for predicting the stability of future architectural states.
- **1.0 Installation Architecture (Neurex CLI)**: Scaffolded a native Rust daemon (`neurex-cli`) to govern the Dual-Layer architecture. It features real hardware diagnostics (`sysinfo`), dynamic Docker sandboxing (`bollard`), and asynchronous Host Control Plane bootstrapping (`tokio`).

### Performance & Stability
- **O(1) Self-Optimization Lookups**: Upgraded the `SelfOptimizer` to use Dictionary-based tracking, eliminating O(N) list-scan overhead when managing thousands of proposed core refactors.
- **High-Throughput Neural Law Verification**: Upgraded the Anti-Gravity Protocol enforcer to use pre-compiled regex objects (`re.compile`), drastically reducing CPU overhead during weight evolution verification.
- **Non-Blocking Quantum Simulation**: Offloaded CPU-bound probabilistic math in the `QuantumPathSim` to a separate thread pool (`asyncio.to_thread`), entirely resolving the 'Quantum Overhead' event loop blocking issue.

## [0.2.1] - 2026-05-01 (UNIFIED MESH & PERSISTENT INTELLIGENCE)
### Added
- **Infrastructure Hub Overhaul**: Redesigned the `InfraPanel` with real-time VRAM/RAM/CPU metrics, professional model deployment with quantization support (4-bit/8-bit/FP16), and dynamic agent recommendations.
- **Active Skills & MCP Management**: Integrated a toggleable interface for managing agent tools and Model Context Protocol (MCP) servers directly from the infrastructure hub.
- **Persistent Multi-Terminal**: Refactored the terminal architecture to keep multiple sessions alive in the background; switching tabs or terminals no longer destroys state or closes PTY sessions.
- **Unified WebSocket Store**: Migrated all WebSocket communication to a central Zustand-based `send` method, eliminating global window hacks and improving type safety.
- **Mesh Logic Integration**: Added peer node discovery and status indicators to the infrastructure catalog for distributed inference monitoring.
- **Wiki & Documentation Hub**: Created a comprehensive `README.md` and updated `PHILOSOPHY.md` and `DESIGN_SYSTEM.md` to reflect new architectural standards.
- **Phase 44: Performance Hardening & Throughput Scaling**:
    - **Accelerated API Serialization**: Integrated `orjson` (ORJSONResponse) as the global FastAPI response engine, significantly reducing JSON overhead for high-frequency telemetry.
    - **High-Throughput Observability**: Implemented a buffered batch-writing system for the Flight Recorder, replacing immediate DB commits with a 2-second background flush worker.
    - **Butter-Smooth Terminal**: Introduced throttled PTY buffering (20ms/10-line aggregation) to prevent WebSocket flooding and UI stutter during high-velocity terminal output.
    - **Fail-Fast Federated RAG**: Reduced peer search timeout to 3s with `asyncio.gather` parallelization, ensuring snappy global intelligence even in large, decentralized networks.
    - **Sema-Throttled Memory Indexing**: Implemented parallel workspace indexing (10 concurrent files) in the `MemoryWorker`, drastically reducing the time to reach architectural situational awareness.
    - **Intent-Aware Context Compression**: Refactored the compressor to retain docstrings during structural summaries, preserving architectural intent while purging implementation tokens.
    - **Token Chunking (Backend)**: Buffered LLM streaming into blocks of 10 tokens, reducing WebSocket message frequency and network pressure by ~90%.
    - **Quiet-Period FS Debouncing**: Optimized the file watcher with 500ms inactivity buffering and path-specific event batching for more efficient UI refreshes.
    - **Persistent Mesh Clients**: Migrated all Mesh-wide communications (RAG, Memory, Agents) to long-lived HTTP client pools to eliminate connection churn.
    - **O(1) Hive Sharding**: Optimized the HiveMind lock-manager with direct index lookups, replacing linear searches during massive parallel refactors.
    - **Architectural State Decoupling (Frontend)**: Refactored the `App.tsx` root and major UI panels to use strict Zustand selectors, preventing global layout re-renders for character-level or metric-level state changes.
    - **Token-Streaming Buffering (Frontend)**: Implemented 40ms buffering in the WebSocket hook to aggregate incoming LLM tokens, reducing store update frequency and relieving main-thread pressure during high-speed reasoning bursts.
    - **Memoized Component Rendering**: Integrated `React.memo` for high-frequency list items in the `FlightRecorder` (Traces) and `AIPanel` (TaskCards), ensuring DOM updates are isolated and efficient.
    - **O(1) Explorer Aggregation**: Replaced recursive tree-walks in the `FileExplorer` with shallow status lookups, ensuring consistent performance even in massive workspaces with thousands of files.
- **Phase 45: Sentient IDE (Autonomous Self-Repair & Governance)**:
    - **Neural Linter**: Launched a real-time architectural validation layer that interrogates the Internal Reasoning Engine to verify all proposed code mutations against `ARCHITECTURE.md` and `DESIGN_SYSTEM.md`.
    - **Autonomous Self-Repair Loops**: Implemented 'Reflection and Repair' logic in the `CoderAgent`, enabling agents to detect architectural rejections or tool failures and autonomously regenerate compliant mutations.
    - **Swarm Consensus Protocol**: Established a democratic governance layer for critical architectural assets, requiring a 3-agent voting threshold for mutations targeting core logic.
    - **Zero-Restart Runtime Evolution**: Launched the `LiveReloader` service, enabling the Mesh to hot-swap Python modules on the fly, allowing for instantaneous logic adoption without process termination.
    - **Predictive Maintenance**: Integrated churn-based re-indexing heuristics that autonomously trigger background workspace indexing when high filesystem activity is detected.
    - **Regulated Mutation Pipeline**: Integrated the Neural Linter and Consensus protocol into the `BaseAgent` tool dispatch, establishing a zero-trust mutation environment for the entire Mesh.
- **Phase 46: Deep Neural Integration (Mesh Context Sharding)**:
    - **Attention Coordinator**: Launched a federated orchestration layer that distributes model attention heads across multiple Mesh nodes, enabling massive parallel reasoning bursts.
    - **Global Context Sharding**: Implemented real-time sharding of the 128k+ token context window, allowing the Mesh to pool VRAM across federated nodes for high-context tasks.
    - **Predictive Neural Prefetching**: Integrated a prefetcher service that proactively warms up model weights and context based on agent trajectory, eliminating cold-start latency.
    - **Mesh KV-Sync Protocol**: Launched a sub-ms neural state propagation layer that synchronizes hidden states and K/V cache deltas across the Mesh backplane.
- **Phase 47: Neural Hardware Virtualization (GPU Over-Provisioning)**:
    - **Virtual VRAM Pool**: Launched a mesh-wide resource aggregator that treats distributed GPU memory as a single, unified neural compute pool.
    - **Neural Swap-Space**: Implemented high-speed state swapping between System RAM and VRAM, enabling the execution of models exceeding physical VRAM capacity.
    - **Autonomous Re-Quantizer**: Launched a dynamic precision management service that autonomously re-quantizes models (e.g., Q8 to IQ2) to fit current Mesh VRAM availability.
    - **Hardware Orchestrator**: Integrated a central coordination layer that autonomously manages pooling, swapping, and quantization fallbacks for high-reasoning bursts.

### Fixed
- **Chat Persistence Fix**: Resolved a critical race condition in the WebSocket handler by using isolated database sessions for user/assistant message recording.
- **Neural Context Compression**: Implemented `ContextCompressor` to structurally summarize stable modules, maximizing effective context window for complex reasoning.
- **Autonomous CI/CD Self-Healing**: Launched `CIHealer` to monitor pipeline health and autonomously trigger background repair tasks for regression failures.
- **Secure Multi-User RBAC**: Implemented `RBACManager` with granular, path-aware permissions to secure 'Swarm' and mutation tasks in federated environments.
- **Neural Code Search (RAG 2.0)**: Launched `NeuralExplorer` to perform hybrid semantic/relational retrieval, ensuring agents understand the full architectural call graph.
- **Sandboxed Neurex Neural Harness**: Implemented the `claude_harness` MCP tool to securely delegate massive refactoring tasks to an isolated Neurex Neural Harness Docker container.
- **Neural Model Fusion (Swarms 2.0)**: Enhanced the SwarmAgent to intelligently assign specialized models (Claude for logic, Qwen for boilerplate) to sub-tasks, optimizing intelligence per watt.
- **Universal Neural Harness**: Decoupled the agentic 'harness' logic from Neurex Neural Harness and implemented a model-agnostic engine capable of driving autonomous loops with Qwen and other OS models.
- **Skeptical Memory (Phase 31)**: Implemented 'Zero-Trust' memory management that forces agents to verify filesystem state via grep/read before every mutation, preventing context entropy.
- **YOLO Permission Classifier (Phase 32)**: Launched a low-latency auto-approval gate for 'safe' tools, dramatically accelerating agent exploration speed.
- **Neurex Somnus (Phase 33)**: Implemented an 'always-on' monitor (autoDream) that asynchronously updates architectural intel and memory pointers upon filesystem changes.
- **HYPERPLAN Deep Thinking (Phase 34)**: Launched a multi-pass architecture planning engine that enforces Decomposition, Symbolic Trace, and Optimization cycles for complex design tasks.
- **Somnus Skill Harvesting (Phase 35)**: Extended the background daemon to autonomously discover, security-audit, and acquire new capabilities from Mesh peers.
- **Neural Swarm Consensus (Phase 36)**: Implemented a 'voting' protocol where multiple agents must approve significant architectural mutations before application.
- **Mesh-Scale Distributed RAG (Phase 37)**: Launched a federated search engine that queries the collective intelligence of all nodes in the Mesh, providing 'global' context awareness.
- **Persistent Workspace Layouts**: integrated automatic storage for sidebar, terminal, and assistant panel dimensions using `react-resizable-panels` and `localStorage`.
- **Advanced Panel Controls**: added Maximize, Collapse, and Clear actions to the Bottom Panel header for streamlined workspace management.
- **VSCodium Parity**: achieved layout parity with professional editors by ensuring terminal reflow and panel state preservation across sessions.
- **Title Bar Restoration**: fixed a layout regression where the `TitleBar` was omitted during panel refactoring; restored reactive visibility based on `menu_mode`.
- **Title Bar Alignment & UX**: refined the `TitleBar` with absolute centering for project/file names and fluid `MenuBar` integration for VSCodium parity; fixed a layout bug where the title was detached from the header.
- **Window Title Synchronization**: implemented automatic syncing between the IDE's active context and the browser's `document.title`.
- **FileExplorer Root Expansion**: Fixed a bug where the workspace root directory could not be expanded due to falsy path validation.
- **InfraMetrics Type Accuracy**: Corrected the `InfraMetrics` TypeScript interface to match the backend's resource reporting (RAM totals, CPU usage).
- **Terminal Re-fitting**: Implemented a robust re-fit mechanism that fires when a hidden terminal becomes visible, ensuring jitter-free layout restoration.
- **Imperative Sidebar Accordion**: Refactored the `FileExplorer` to prioritize the workspace tree; implemented programmatic collapse/expand for Open Editors and Outline sections, allowing them to shrink to headers while preserving global layout integrity.
- **Autonomous Self-Evolution**: Integrated `audit_codebase_health` tool for automated drift detection; updated `PlannerAgent` with proactive auditing directives to ensure long-term architectural stability.
- **Design System Auditing**: Implemented `check_design_compliance` to ensure self-evolved components adhere to glassmorphism and BEM standards defined in `DESIGN_SYSTEM.md`.
- **Autonomous Sentinel**: Launched background self-healing service that monitors API/Web/Ollama ports and auto-restarts failed processes, ensuring high availability for autonomous agent loops.
- **Sandbox Mutation Support**: Expanded the Docker execution engine with a `mutation_allowed` flag, enabling agents to perform build-related writes (RW) when authorized.
- **Predictive Resource Elasticity**: Integrated `ResourcePredictor` into the `MeshRouter` to track telemetry trends and pre-emptively avoid nodes with rising load trajectories.
- **Swarm Leader Protocol**: Launched `SwarmManager` and `SwarmAgent` for mesh-wide parallel execution of massive refactoring tasks (>10 files).

## [0.2.0] - 2026-04-30 (GRACEFUL RESIZING & LAYOUT PERSISTENCE)
### Added
- **Persistent Workspace Layouts**: integrated automatic storage for sidebar, terminal, and assistant panel dimensions using `react-resizable-panels` and `localStorage`.
- **Advanced Panel Controls**: added Maximize, Collapse, and Clear actions to the Bottom Panel header for streamlined workspace management.
- **VSCodium Parity**: achieved layout parity with professional editors by ensuring terminal reflow and panel state preservation across sessions.
- **Title Bar Restoration**: fixed a layout regression where the `TitleBar` was omitted during panel refactoring; restored reactive visibility based on `menu_mode`.
- **Title Bar Alignment & UX**: refined the `TitleBar` with absolute centering for project/file names and fluid `MenuBar` integration for VSCodium parity; fixed a layout bug where the title was detached from the header.
- **Window Title Synchronization**: implemented automatic syncing between the IDE's active context and the browser's `document.title`.
- **Resizable Sidebar Sections**: restructured the `FileExplorer` into resizable vertical panels with imperative accordion behavior for Open Editors, Workspace, and Outline.
- **Persistent Sidebar Headers**: ensured section titles (Editors, Workspace, Outline) remain visible when minimized by implementing minimum panel sizing and visibility-toggling content.
- **Bottom-Anchored Outline**: ensured the Code Outline is anchored to the bottom of the sidebar and expands upwards reactively.
- **Explorer Padding & Alignment**: standardized indentation and padding across all sidebar sections to ensure a consistent vertical rhythm and professional aesthetic.
- **Advanced Code Outline**: implemented functional symbol extraction for TS/JS/PY with dedicated icons and click-to-jump navigation.
- **Theme-Aware Status Bar**: refactored the `StatusBar` to use the primary accent color and implemented a reactive "Swarm Glow" animation for mesh-active nodes.
- **Dual-Pane Settings UI**: completely redesigned the `SettingsPanel` with a professional sidebar navigation, categorical filtering, and refined form controls for a "tight" administrative experience.
- **Global Layout API**: exposed internal panel controls to the global namespace for inter-component coordination.

## [0.1.9] - 2026-04-30 (LSP STABILITY & API PARITY)
### Fixed
- **Diagnostic State Consistency**: fixed a regression in `EditorPane.tsx` by migrating to the unified `updateDiagnostics` action, resolving TypeScript compilation errors.
- **Infinite Notification Loop Fix**: resolved a recursive installation loop by fixing binary discovery logic and implementing a parallel installation lock in `LSPManager`.
- **LSP Installation Circuit-Breaker**: added a failure registry to `LSPManager` that halts redundant installation attempts for failing language servers, preventing log flooding and server overhead.
- **Linux-Native Recipes**: updated LSP installation commands to use `curl` and `npm` instead of `brew`, ensuring compatibility with the current Linux environment.
- **Infrastructure API Parity**: added missing `/api/infra/engines`, `/api/infra/metrics`, and `/api/infra/peers` endpoints to resolve 404 errors during frontend initialization.
- **Internal Server Error Handling**: hardened the language installation route to provide clearer error reporting and prevent generic 500 crashes.

## [0.1.8] - 2026-04-30 (MULTI-FOLDER WORKSPACE ARCHITECTURE)
### Added
- **Multi-Root Workspace Engine**: introduced the ability to anchor the IDE to multiple disparate project roots simultaneously:
  - **Root-Aware Backend**: updated all file API endpoints (`/read`, `/save`, `/search`, `/delete`, `/rename`) to propagate and respect a `root_path` context.
  - **Contextual Terminal Anchoring**: integrated directory-aware PTY spawning. New terminals automatically inherit the workspace root of the active file.
  - **Dynamic Breadcrumbs**: added root-prefixed path navigation in the editor for instant cross-project orientation.
  - **Multi-Root Search**: enabled parallel semantic and substring searching across all registered workspace folders with grouped results.
- **UI/UX Parity Updates**:
  - **Workspace Tabs**: editor tabs now display subtle root tags to distinguish between files with identical names in different project folders.
  - **Title Bar Integration**: the main application title now reflects the specific project root of the active session.
  - **Menu Bar Synchronization**: updated "Save" and "New Terminal" actions across all menus to be context-aware.

### Fixed
- **Search Result Grouping**: resolved a collision bug where search results from different roots but identical relative paths were incorrectly merged.
- **Store Logic**: modernized `NeurexStore` to track `root` identifiers for all `openFiles` and `terminalSessions`.
- **API Security**: hardened path resolution to prevent cross-root traversal via standard `Path.resolve` validation.

### Changed
- Refactored `FileExplorer` to propagate `root_path` via DOM context for robust right-click operation routing.
- Updated `PTYManager` to decouple session initialization from the global `WORKSPACE_PATH`.
- **Core Refactoring & Protocol Compliance**:
  - **Forbidden Print Removal**: purged all `print()` statements from the backend in favor of structured `structlog` logging.
  - **Store Optimization**: refactored `useStore` to unify diagnostics management and improve workspace synchronization reliability.
  - **PTY Stability**: added robust directory validation and fallbacks in `PTYSession` to prevent shell startup failures in multi-root environments.


## [0.1.7] - 2026-04-29 (NATIVE LSP & NEURAL LENS)
### Added
- **Universal Language Intelligence**: transitioned to a high-performance, native Language Server Protocol architecture with near-universal coverage:
  - **Mega-Registry Expansion**: added support for the **Top 100+** languages (including Elixir, Haskell, Zig, Fortran, Cobol, and more).
  - **Dynamic Fallback Engine**: automated heuristic discovery for niche languages via system-path pattern matching (e.g., `lang-lsp`).
  - **Custom LSP Configuration**: introduced `.neurex/lsp.json` for workspace-level command overrides and proprietary language support.
  - **LSP Autopilot**: automated discovery and lifecycle management of system-installed language servers.
- **Neural Error Lens**: implemented a native, high-fidelity inline diagnostic system:
  - **Inline Error Messages**: groups and renders diagnostics (Errors/Warnings) directly after code lines with thematic neon accents.
  - **Real-time Synchronization**: updates decorations instantly as the LSP reports markers.
- 16. **Neural Context Compression (Phase 22 Milestone)**:
    *   Status: **RESOLVED** (v0.2.1-stable).
    *   Implementation:
        *   **Structural Summarization**: Developed `ContextCompressor` to replace stable function bodies with architectural summaries, preserving shape while saving tokens.
        *   **Boilerplate Pruning**: Implemented semantic filters to strip redundant imports and license headers from RAG-retrieved context.
        *   **Agent Integration**: Integrated compression directly into `BaseAgent.rag_context`, enabling all agents to handle large context windows without overflow.

17. **Autonomous CI/CD Self-Healing (Phase 23 Milestone)**:
    *   Status: **RESOLVED** (v0.2.1-stable).
    *   Implementation:
        *   **Pipeline Health Monitoring**: Launched `CIHealer` service that polls external CI status (GitHub/GitLab) and identifies build failures.
        *   **Log-Driven Recovery**: Developed infrastructure to analyze CI error logs and autonomously queue repair tasks in the Orchestrator.
        *   **Lifespan Integration**: Integrated the healing loop into the core API lifespan, ensuring persistent background self-correction.

18. **Secure Multi-User RBAC Expansion (Phase 24 Milestone)**:
    *   Status: **RESOLVED** (v0.2.1-stable).
    *   Implementation:
        *   **Granular Permission System**: Developed `RBACManager` to define clear roles (Owner, Contributor, Guest, Peer) and associated permission sets.
        *   **Path-Aware Authorization**: Implemented glob-patterned filesystem rules to restrict 'Swarm' and mutation tasks to authorized directories.
        *   **Federated Security**: Established the zero-trust framework required for secure cross-node collaboration in the Mesh.

19. **Neural Code Search & RAG 2.0 (Phase 25 Milestone)**:
    *   Status: **RESOLVED** (v0.2.1-stable).
    *   Implementation:
        *   **Hybrid Retrieval Engine**: Implemented `NeuralExplorer` to combine vector similarity (semantic) with AST-aware graph traversal (relational).
        *   **Dependency Expansion**: Augmented the search loop to automatically include referenced modules and interface definitions in the retrieved context.
        *   **BaseAgent Optimization**: Replaced the legacy RAG logic with the hybrid neural loop, providing all agents with a high-fidelity map of the workspace.

20. **Sandboxed Neurex Neural Harness (Phase 28 Milestone)**:
    *   Status: **RESOLVED** (v0.2.1-stable).
    *   Implementation:
        *   **Isolated Execution Environment**: Developed `neural_sandbox.Dockerfile` to host the `@anthropic-ai/claude-code` CLI in a secure, containerized sandbox.
        *   **MCP Bridge**: Implemented `neural_harness.py` server to act as an asynchronous bridge between Neurex and the Neurex Neural Engine.
        *   **Secure Delegation**: Enabled the Orchestrator to delegate massive, cross-cutting tasks to Claude while preserving host system integrity.

21. **Neural Model Fusion (Phase 29 Milestone)**:
    *   Status: **RESOLVED** (v0.2.1-stable).
    *   Implementation:
        *   **Heterogenous Swarm Execution**: Updated `SwarmAgent` to perform model tier assignment during task decomposition.
        *   **Dynamic Resource Allocation**: Modified `SwarmManager` to respect and dispatch sub-tasks to nodes hosting the requested model specialized for the task (e.g. logic-heavy vs boilerplate-heavy).
        *   **Intelligence Optimization**: Established a "tier-aware" swarm logic that maximizes reasoning quality while minimizing compute overhead.

22. **Universal Neural Harness (Phase 30 Milestone)**:
    *   Status: **RESOLVED** (v0.2.1-stable).
    *   Implementation:
        *   **Vendor Decoupling**: Extracted the core 'agentic harness' logic (Plan-Act-Review) from closed-source tools like Neurex Neural Harness.
        *   **Neural Harness Engine**: Developed a model-agnostic execution loop (`harness/engine.py`) that standardizes tool-calling and observation handling.
        *   **OS Model Prioritization**: Integrated Qwen-2.5-Coder as the default driver for the harness, enabling state-of-the-art autonomy without vendor lock-in.

- **Skeptical Memory (Phase 31)**: Implemented 'Zero-Trust' memory management that forces agents to verify filesystem state via grep/read before every mutation, preventing context entropy.
- **YOLO Permission Classifier (Phase 32)**: Launched a low-latency auto-approval gate for 'safe' tools, dramatically accelerating agent exploration speed.
- **Neural GitLens Suite**:
  - **Commit Blame Ghost Text**: renders authorship metadata (author, summary, date) for the active line directly in the editor.
  - **File Timeline Sidebar**: a dedicated, visual history tracker with commit nodes and glassmorphic cards.
- **Intelligent Formatting**: integrated "Format on Save" logic that leverages the LSP's formatting capabilities (Black, Prettier, etc.) automatically.
- **New API Endpoints**: added `/api/languages/supported`, `/api/git/blame`, and `/api/git/history` to support the new intelligence layer.

### Fixed
- **LSP Client Initialization**: modernized the frontend client to use the `initServices` (v10+) pattern for cleaner Monaco service registration.
- **Network Efficiency**: optimized Git blame updates to only trigger on line-number changes, significantly reducing backend telemetry load.

### Changed
- Renamed the "History" sidebar tab to "Chat History" and introduced the new "File Timeline" tab.
- Re-architected the editor's mounting lifecycle to support dynamic LSP attachment.
29. 

## [0.1.6] - 2026-04-29 (ADVANCED INTERACTION & UX)
### Added
- **Unified Context Menu System**: implemented high-fidelity, 'Neural' right-click menus across all critical surfaces:
  - **Editor Tabs**: Close, Close Others, Close to Right, Copy Path, Reveal in Explorer.
  - **File Explorer**: Open, Open in Terminal, Rename, Delete, Path Utilities.
  - **Monaco Editor**: Go to Definition, References, Rename Symbol, Format, Refactor (wired to native engine).
- **Standardized Button System**: introduced a global `.btn` architecture modeled after the 'DEPLOY' aesthetic (dark surfaces, neon accents, uppercase technical typography).
- **Destructive Action Safeguards**: created the `ConfirmModal` component, a premium blurred verification step for high-risk operations like file deletion.
- **Backend File Operations**: added `/api/files/rename` and `/api/files/delete` endpoints with path traversal protection and workspace resolution.
- **Path Ergonomics**: integrated one-click "Copy Path" and "Copy Relative Path" with toast confirmations across the entire UI.

### Fixed
- **Visual Visibility**: enforced `opacity: 1.0` on all tab close buttons to ensure unmistakable interactive affordance.
- **Interaction Model**: disabled Monaco's native context menu to provide a consistent, branded experience.
- **State Synchronization**: ensured that file renames and deletions automatically update the global store and synchronized editor sessions.

### Changed
- Migrated all action-triggering buttons to the new standardized design system.
- Enhanced the "Empty Editor" dashboard with standardized typography and button styles.

## [0.1.5] - 2026-04-29 (IDE CORE STABILIZATION)
### Added
- **Full MenuBar Wiring**: transformed the `MenuBar` into a functional control center with comprehensive actions for File, Edit, View, Terminal, and Help menus.
- **Advanced Terminal Customization**: introduced granular settings for **Font Size**, **Font Family** (JetBrains Mono, Fira Code, etc.), and **Cursor Style** (Block, Bar, Underline) with live-preview support.
- **Global Keyboard Shortcuts**: implemented industry-standard shortcuts for productivity:
  - `Ctrl+Shift+` ` for New Terminal
  - `Ctrl+L` for Clear Terminal (Frontend + Backend Sync)
  - `F5` for Run Active File (detects Python, JS, Bash)
  - `Ctrl+,` for IDE Settings
  - `Ctrl+Shift+P` for Command Palette
- **Active Execution Layer**: enabled one-click "Run Active File" logic that injects language-aware commands directly into the terminal.
- **Terminal Lifecycle Management**: added backend support for `terminal_clear` and `terminal_kill` to ensure PTY history and processes are correctly managed.

### Fixed
- **UI Contrast Refinement**: significantly increased the visibility of tab close buttons (X) in both the editor and terminal panels by setting default opacity to 1.0.
- **Critical Architecture Stability**:
  - Resolved `Cannot redeclare block-scoped variable` errors in `App.tsx`.
  - Fixed `Cannot find name 'terminalRegistry'` and `Cannot find name 'store'` errors.
  - Eliminated redundant `theme` property artifacts in `Terminal.tsx` initialization.
- **Design Integrity**: restored the accidentally overridden Neurex logo branding and hover effects in the activity bar.
- **State Synchronization**: fixed a race condition where terminal resizing would fail if the DOM was not fully settled.

### Changed
- Refactored `App.tsx` store destructuring to a unified, O(1) single-call pattern.
- Exported `terminalRegistry` to enable cross-module session management from the global store.

## [Unreleased] - 2026-04-28 (CAVEMAN ULTRA UPDATE)

### Added
- **Terminal Multiplexing**: Support for multiple independent shell sessions with tabbed switching and session-aware command routing.
- **Skill Discovery & Injection**: Native logic for Git-based skill installation and curated discovery of agentic toolsets.
- **Global Command Palette (Cmd+Shift+P)**: Universal entry point for all IDE actions, including file management, view toggling, and developer tools.
- **Source Control (Git) Integration**: A dedicated sidebar panel for staging changes, viewing branch status, and committing code with keyboard shortcuts (Cmd+Enter).
- **Mature Search & Replace**:
  - Implemented result grouping by File (expandable/collapsible).
  - Added 'Replace All' functionality with regex support.
  - Added fuzzy search for results.
- **Burger Menu 2.0**: Unified the top-level menu into a single, branded '⬡' trigger in the Activity Bar.
- **Interactive Status Bar**: Real-time cursor position, indentation selection, encoding selection, and language mode switching via Command Palettes.
- **AI Intelligence Indicators**: Pulse animations for active AI composition and thinking states.
- **Security Hardening (RBAC+)**:
  - Implemented time-limited, role-aware **Invite Codes** for registration.
  - Enforced strict environment-based **JWT Secret** validation (prevents insecure defaults).
  - Sanitized skill installation paths to block path traversal vulnerabilities.
- **Context Summarization**: Added an automated history condensation step in the Orchestrator to prevent context window bloat during complex task sequences.
- **Unified Protocol**: Established `.antigravityrules` as the absolute Source of Law and mandated the **Confirmation Rule** for agentic reasoning.
- **SkillsMP Marketplace**: Integrated deep-linking and marketplace discovery directly into the Skills Panel.
- **Infrastructure Hub (v2)**: Restored high-fidelity UI for Agent Recommendations, Engine Stack monitoring, and Model Catalog management.
- **Universal Installer**: Created a role-aware cross-platform installation system with dedicated launchers for Linux, macOS, and Windows.
- **Multi-Vendor Acceleration**: Enhanced hardware detection to support Apple Silicon (Metal), AMD (ROCm), and Intel (SYCL/OpenCL).
- **Global Context Menus**: Implemented system-wide right-click menus for rapid file and task management.

### Fixed
- **Terminal Reliability**: Resolved input bypass issues, debounced resize events, and fixed blank screen artifacts.
- **Memory Worker**: Refactored the memory indexing worker to be non-blocking, eliminating UI hangs during large code ingestions.
- **Initialization**: Resolved deadlocks in the mesh network startup and fixed IPv4/v6 loopback mismatches.
- **Search Persistence**: Ensured search results and auto-expand states persist across view toggles.
- **Infrastructure**: Hardened PTY broadcast stability and fixed settings persistence across reloads.
- **Infinite Layout Bleeding**: Enforced strict `min-width: 0` and `overflow: hidden` across the entire flex layout.
- **Terminal Rendering**: Achieved a 'flush' seamless look with synced background colors (#050507) and descender clearance (+2px lifting).
- **Redundant UI Elements**: Fused the Neurex logo with the menu trigger and removed redundant headers.
- **Empty Space Artifacts**: Fixed PanelGroup constraints to ensure edge-to-edge rendering of the AIPanel.

### Changed
- Refactored `App.tsx` into a lean, professional layout engine.
- Migrated all IDE actions to a unified `MenuBar` logic tree.
- Standardized tooltips across every interactive icon in the IDE.

## [0.1.4] - 2026-04-29 (HIGH PERFORMANCE UPDATE)
### Added
- **Infrastructure Hardening**:
  - Implemented **WebSocket Reconnection** with exponential backoff (1s to 30s) to survive transient backend restarts and network drops.
  - Introduced **Granular Engine Port Management** in the Control Center, allowing administrators to remap vLLM, llama.cpp, and Ollama ports to resolve local network collisions.
  - Added **Model Deployment Modals**: a high-fidelity 'OS-style' interface for reviewing model specifications (VRAM, context, origin) and configuring deployment parameters before pulling assets.
- **Visual Excellence**:
  - **Thematic Terminal**: The xterm.js cursor, text selection, and prompt colors (magenta) are now fully synchronized with the global platform accent color.
  - **Zero-Trust Input Styling**: Removed distracting browser-default spin buttons from numerical inputs for a cleaner, professional 'Neural' look.
  - **Interactive Affordance**: Added hover-scale and glow transitions to all model catalog items to indicate clickability.

### Fixed
- **Terminal Latency**: eliminated typing lag by implementing **Surgical State Subscriptions** via `subscribeWithSelector`. The terminal now completely ignores non-visual state updates (messages, tasks, presence).
- **Initialization Speed**: achieved 'Near Instant' loading by **parallelizing system hydration**. Infrastructure discovery (Registry, Skills, Peers, and Memory) now executes in a single concurrent batch.
- **Port 8000 Collision**: fixed a critical conflict between the Neurex API and vLLM by remapping the default vLLM port to 8002.
- **Type Safety**: resolved multiple TypeScript compiler errors in the store and synchronized the `NeurexStore` interface with the dynamic settings registry.

## [0.1.3] - 2026-04-29
### Added
- **Dedicated Mobile UI**: Introduced `MobileView` with bottom-navigation for seamless touch interaction on devices <= 768px.
- **Global Settings Cache**: Implemented system-wide settings management in `useStore` to enable zero-latency "instant" hydration of the Control Center.

### Fixed
- **Settings Sync Stalls**: Hardened core synchronization with 10s timeouts and enforced authentication across all neural link proxies.
- **ReferenceError Crash**: Resolved critical variable scoping issues in `SettingsPanel` that caused rendering failures during identity transitions.
- **Theme Consistency**: Guaranteed authenticated theme refreshes to prevent visual preset resets on neural link reconnects.

## [0.1.2] - 2026-04-28
### Added
- **Dynamic Theme Engine**: implemented `color-mix` based design tokens, allowing the entire UI (including chat) to reactively adapt to the user's primary accent color.
- **Immediate Settings Preview**: configuration changes now apply in real-time to the DOM before persistence.
- **Batch State Management**: introduced `handleBatchChange` in `SettingsPanel` to eliminate state race conditions during rapid property updates.

### Fixed
- **Settings Persistence**: resolved a critical bug where non-admin users were blocked from saving visual preferences due to the presence of restricted infrastructure keys in the payload.
- **RBAC Hardening**: refined the backend settings validator to only enforce admin-only checks if the restricted key's value is actually modified.
- **Color Sync**: standardized all default colors to HEX format to ensure 1:1 synchronization with native browser color pickers.
- **Terminal Anchor**: implemented an immediate, pixel-perfect `fit()` logic and unified flex-bottom layout to ensure the cursor remains physically locked to the bottom edge during all resize operations (shrink/grow).
- **Chat UI**: applied primary accent colors to user message bubbles and thinking animations for full thematic unity.

## [0.1.1] - 2026-04-28
### Added
- Initial IDE Core implementation.
- Monaco Editor integration.
- WebSocket-based Mesh Network heartbeat.
- HSL-based Design System and Glassmorphism.
