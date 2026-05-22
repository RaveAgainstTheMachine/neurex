# Changelog

All notable changes to the Neurex project will be documented in this file.

## [0.6.0] - 2026-05-22: THE INTERACTIVE AGENTIC PIVOT
### Added
- **Pillar 1: Visual Agent Task Graph Editor**: Designed and built an interactive node-based designer canvas using SVG edges and glassmorphism styling. Supports on-graph rewiring of dependencies, inline node editing, manual step insertions, parent-child deletion auto-rewiring, and full-screen visualization overlays.
- **Pillar 2: Multi-Cursor AI Pair Programming**: Implemented real-time streaming cursor telemetry at 60Hz. Decorates Monaco Editor with neon gradient agent cursors (`[Neurex Coder]`) and pulsing micro-animations.
- **Pillar 3: Bidirectional LSP Context Router**: Developed an LSP multiplexer supporting Definition lookup, Reference searching, Hover signatures, and Diagnostic tracking. Registered these capabilities as native tools inside the dynamic agent tool capability loop.
- **Pillar 4: Visual MCP Tool Sandbox & Manager**: Built a dedicated permissions panel displaying connected Model Context Protocol servers and schemas. Enables granular permissions override (Always Allow, Always Ask, Deny) and manual execution playgrounds.
- **Pillar 5: Reliability, Evals & Controls**: Implemented a Zero-Diff Staging Guard routing agent writes/diffs safely to `.neurex/staging` under staging mode, tracked deletions via `.deleted` marker files, exposed chronological reasoning traces via Teleplay Replay endpoint, launched async lifespan Startup Dependency Audits, and gated GitHub Actions CI on hermetic `.venv` test runs.
- **Phase 6: Observability Playback Canvas & Simulation Benchmarks**: Formulated a multi-stage background simulation runner routing via `POST /api/benchmarks/run` and `GET /api/benchmarks/status`. Created a cron/pulse-controlled scrubbing timeline player (TelemetryReplayCanvas) with Live Sync locking mechanism, and a glassmorphic visual arena scoreboard (BenchmarkDashboard) for complete execution tracking.


## [0.5.6] - 2026-05-22: MONACO INLINE AI EDITING
### Added
- **Monaco Inline AI Edit (`Ctrl+K`) Loop**: Implemented a near-instant interactive inline refactoring loop. Captures `neurex_inline_edit` custom events from Monaco and routes them directly to a fast-path streaming agent execution, bypassing standard multi-step planner graphs.
- **Fast-Track Stream Generation**: Added `execute_inline_edit` to the `Orchestrator` to stream refactored content, with custom markdown fence filtering to deliver clean code straight to Monaco's side-by-side `<DiffEditor>`.
- **WebSocket Route Binding**: Wired `inline_edit` messages in `websocket.py` to route requests dynamically to the streaming orchestrator path.
- **Robust Verification & Testing**: Added diagnostic coverage and unit tests in `test_orchestrator.py` covering mock environments and live-streaming token extraction.

## [0.5.5] - 2026-05-11: ARCHITECTURAL GROUNDING & HOT-RELOADING
### Added
- **Sentient IDE Hot-Reloading**: Implemented a central `AgentRegistry` and `HotReloadManager` that allows the API to dynamically reload agent logic (e.g., `CoderAgent`) on file save without a server restart.
- **Fail-Fast Orchestration**: Hardened the `Orchestrator` to halt graph execution immediately upon task failure, ensuring sequential integrity and preventing cascading agentic errors.
- **Deep Integration Testing**: Established a new integration test suite (`tests/test_integration_scenarios.py`) covering partial approvals, failure halts, and sequential dependency validation.
- **Mock LLM Optimization**: Updated the orchestration loop to bypass Git snapshots when in `mock` mode, significantly accelerating the evaluation and testing feedback loop.

### Changed
- **Architectural Purge**: Quarantined 7 speculative or orphaned modules (Swarm Management, Genetic Evolution, Mesh Governance) to reduce architectural noise and focus on production-ready features.
- **Linting Rigor**: Updated `ruff.toml` to enforce strict compliance while excluding quarantined code, achieving a 100% green status across the active codebase.
- **Authentication Resilience**: Validated JWT-based WebSocket authentication for non-interactive clients (Eval Harness), resolving 1008 policy violations.

## [0.5.4] - 2026-05-10: GROUNDED SECURITY
### Added
- **Documentation Grounding**: Rewrote core documentation (Architecture, Roadmap, README) to align with actual implementation and remove speculative buzzwords.
- **Protocol Enforcement**: Updated `.projectrules` to mandate grounded, technical documentation.
- **Security Hardening**: Hardened subprocess calls, SSRF protection, and path traversal mitigation.
- **Dependency Automation**: Synchronized mesh components and resolved `bollard` v0.21.0 migration breaks.

## [0.5.3] - 2026-05-10: [IMMUTABLE RELEASE]
*Note: This release was marked as immutable on GitHub and contains fragmented state. Please use v0.5.4.*

### Changed
- **CLI Dependency Bump**: Upgraded `bollard` to `0.21.0` and `tungstenite` to `0.29.0`, fixing major API breaks.

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
