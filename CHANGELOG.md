# Changelog

All notable changes to the Neurex project will be documented in this file.

## [0.5.2] - 2026-05-09: THE STABLE SUBSTRATE
### Added
- **Release Automation**: Full GitHub Actions pipeline for automated Docker Hub builds (API, Web, Sandbox) and multi-platform CLI binary distribution (Linux, macOS, Windows).
- **Community Standards**: Established official `CODE_OF_CONDUCT.md`, `SECURITY.md`, and high-fidelity Issue/PR templates.
- **Unified Branding**: Refined the "About Neurex" identity, focusing on the "Autonomous Engineering Workspace" positioning.
- **High-Fidelity About Modal**: Added a glassmorphic about panel with dynamic versioning and hardware telemetry.
- **Production Web Stack**: Implemented Nginx-based production serving for the frontend with SPA routing support.

### Changed
- **Version Unification**: Synchronized all mesh components (API, CLI, Web) to v0.5.2.
- **CLI Networking**: Switched to `rustls-tls` for zero-dependency cross-platform networking.
- **Build Optimization**: Parallelized frontend and backend build steps in the release chain.

## [0.4.1] - 2026-05-03: DYNAMIC ROUTING & DERIVATION
### Added
- **Autonomous Parameter Derivation**: Eliminated manual parameter configuration. The substrate now autonomously extracts model sizes (e.g., 14B, 7B) from Ollama and Hugging Face metadata.
- **Dynamic Model Routing Grid**: Rebuilt the `InfraPanel` with a high-density grid for managing cognitive role-to-model mappings (Planning, Coding, Reviewing).
- **Unified Parameter Resolution**: Hardened the `Orchestrator` to dynamically resolve missing parameters from the source of truth.

### Fixed
- **Orchestrator Stability**: Resolved critical race conditions in the task execution loop.
- **Neural Gradient Rendering**: Fixed CSS text-clipping effects across Safari and Firefox.

## [0.4.0] - 2026-05-03: SECURE MESH INFRASTRUCTURE
### Added
- **Secure Mesh Sovereignty**: Enforced mandatory mTLS and SSL/TLS encryption for all mesh-wide communications.
- **Autonomous Protocol Upgrade**: Implemented a browser-side sentinel for automatic HTTP -> HTTPS upgrades.
- **Dual-Protocol Coherence**: Re-engineered the web server to handle simultaneous HTTP/HTTPS handshakes.
- **Transparent Proxy Infrastructure**: Integrated `X-Forwarded-*` headers for robust backend identity awareness.

## [0.3.5] - 2026-05-01: THE TRIPLE-TIER SUBSTRATE
### Added
- **Triple-Tier Execution Plane**: Implemented a resilient, multi-stage sandboxing architecture:
    - **Performance Tier**: Docker-based containers with GPU acceleration.
    - **Portability Tier**: WASM/WASI execution via `wasmtime`.
    - **Reliability Tier**: Native Rust jailed filesystem fallback.
- **Substrate Dashboard**: Real-time glassmorphic visualizer for execution tier health and hardware telemetry.
- **Proactive Provisioner**: Launched `neurex provision` for autonomous hardware-aware environment setup.

## [0.3.0] - 2026-05-01: MESH COORDINATION
### Added
- **Neural Hardware Virtualization**: Mesh-wide resource aggregator that treats distributed GPU memory as a unified compute pool.
- **Adapter Orchestration**: Dynamic, domain-specific LoRA hot-swapping during inference cycles.
- **Swarm Leader Protocol**: Launched `SwarmManager` for parallel execution of massive refactoring tasks (>10 files).
- **Consensus Dashboard**: UI for overseeing substrate bridges and protocol alignment.

## [0.2.1] - 2026-05-01: PERSISTENT INTELLIGENCE
### Added
- **Context Summarization**: Implemented `ContextCompressor` to structurally summarize stable modules, maximizing effective context windows.
- **Neural Code Search (RAG 2.0)**: Launched `NeuralExplorer` for hybrid semantic/relational retrieval using AST-aware graph traversal.
- **Persistent Multi-Terminal**: Refactored terminal architecture to maintain PTY state across workspace transitions.

## [0.2.0] - 2026-04-30: WORKSPACE ARCHITECTURE
### Added
- **Multi-Root Workspace Engine**: Ability to anchor the IDE to multiple disparate project roots simultaneously.
- **Persistent Layouts**: Automatic storage of sidebar, terminal, and panel dimensions.
- **Advanced Code Outline**: Functional symbol extraction for TS/JS/PY with click-to-jump navigation.

## [0.1.7] - 2026-04-29: NATIVE LSP & DIAGNOSTICS
### Added
- **Universal Language Intelligence**: Native LSP architecture with support for the Top 100+ languages.
- **Neural Error Lens**: High-fidelity inline diagnostic system with neon accents.
- **GitLens Suite**: Commit blame ghost text and file history timeline.

## [0.1.0] - 2026-04-28: INITIAL CORE
### Added
- **Monaco Editor Integration**: Full-featured code editor with Neurex theme.
- **Mesh Network Heartbeat**: WebSocket-based peer discovery.
- **Glassmorphic Design System**: HSL-based design tokens and premium UI substrate.
