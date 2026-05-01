# Project Changelog

All notable changes to the Neurex project are documented in this unified changelog.

## [0.3.3] - 2026-05-01: Neural Temporal Synthesis & Transcendence Performance
### Added
- **Phase 53: Neural Temporal Synthesis**: Initiated temporal state snapshotting and quantum architectural simulation.
- **Neural Temporal Registry**: Enabled the Mesh to capture and restore its entire neural soul (weights/context).
- **Quantum Path Simulator**: Implemented probabilistic branching for predicting the stability of future architectural states.

### Performance & Stability
- **O(1) Self-Optimization Lookups**: Upgraded the `SelfOptimizer` to use Dictionary-based tracking, eliminating O(N) list-scan overhead when managing thousands of proposed core refactors.
- **High-Throughput Neural Law Verification**: Upgraded the Anti-Gravity Protocol enforcer to use pre-compiled regex objects (`re.compile`), drastically reducing CPU overhead during weight evolution verification.
- **Non-Blocking Quantum Simulation**: Offloaded CPU-bound probabilistic math in the `QuantumPathSim` to a separate thread pool (`asyncio.to_thread`), entirely resolving the 'Quantum Overhead' event loop blocking issue.

## [0.3.2] - 2026-05-01: Universal Neural Consensus
### Added
- **Phase 52: Universal Neural Consensus**: Achieved global substrate coherence and protocol-aligned omniscience.
- **Substrate Synchronizer**: Enabled bridging with external decentralized compute networks (Akash/Render).
- **Neural Law Engine**: Enforced the Anti-Gravity Protocol at the neural weight level during evolution.
- **Consensus Dashboard**: High-fidelity frontend for overseeing substrate bridges and protocol alignment.

## [0.3.1] - 2026-05-01: Neural Self-Synthesis
### Added
- **Phase 51: Neural Self-Synthesis**: Initiated autonomous codebase inception and recursive self-improvement.
- **Project Inceptor**: Enabled the Mesh to autonomously spawn sub-projects and microservices.
- **Recursive Self-Optimizer**: Implemented autonomous core infrastructure refactoring based on performance telemetry.

## [0.3.0] - 2026-05-01: THE SENTIENT SINGULARITY
### Added
- **Phase 50: The Sentient Singularity**: Implemented autonomous goal setting and self-generating plugins, enabling the Mesh to direct its own evolution.
- **Phase 49: Neural Collective Intelligence**: Introduced decentralized knowledge distillation and privacy-preserving federated learning across projects.
- **Phase 48: Neural Evolution**: Deployed the Evolution Coordinator for autonomous adapter fine-tuning and architecture mutation (Rank/Module resizing).
- **Singularity Dashboard**: High-fidelity frontend for overseeing Mesh-directed goals and self-generated capabilities.
- **Evolutionary Panel**: Real-time visualizer for neural substrate specialization and adapter fitness scores.
- **Federated Weight Propagation**: Sub-ms synchronization of evolved neural weights across all Mesh nodes.
- **Adapter Orchestration**: Dynamic, domain-specific LoRA hot-swapping during inference cycles.

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
