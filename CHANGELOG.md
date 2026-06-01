# Changelog

All notable changes to the Neurex project will be documented in this file.

## [0.13.0] - 2026-06-01: DYNAMIC WORKSPACE, OPT-IN CONSENSUS & SAFE WRITE AUTO-APPROVALS
### Added
- **Dynamic Workspace Binding**: Switched from hardcoded workspace baselines to reactive environment variable bindings on UI path changes.
- **Opt-In Swarm Consensus**: Converted the global Swarm Consensus protocol into a user setting (`consensus_enabled`, defaulting to False). Added predictive WebSocket notifications suggesting consensus activations during existing file modifications.
- **Safe-Write HITL Bypass**: Introduced auto-approvals for new file creations under Limited autonomy levels, entirely bypassing the human confirmation queue.
- **Single-Step Plan Execution**: Enabled task graphs with a single non-planner execution node to run automatically without manual plan approvals.
- **Structured MCP Results**: Restructured tool responses as JSON envelopes indicating strict success/error states to optimize model reasoning loops.

### Fixed
- **Double Lock Deadlock**: Purged filesystem-level duplicate lock acquisitions causing agents to deadlock against themselves.
- **Unified Model Resolution**: Patched Orchestrator shell resumption paths to resolve cognitive agent roles via Route Maps.
- **Early Linter Return**: Upgraded the Neural Linter to return early without server overhead when standard documents do not exist in the active workspace.

## [0.12.1] - 2026-05-28: UNMOCKED E2E CHAT TESTS & ORCHESTRATOR HITL BUG FIXES
### Added
- **Unmocked E2E Chat Integration Test**: Added high-fidelity integration test in `tests/test_chat_unmocked.py` that exercises the direct Orchestrator chat workflow asynchronously, executing tool dispatch and interactive Human-in-the-Loop resume triggers without heavy socket mocks.
### Fixed
- **Agent Streaming Infinite Loop**: Resolved a critical deadlock in `BaseAgent.stream` where tool history loops caused infinite generation steps under standard mock LLM conditions.
- **Approved Tool Execution Bypass**: Fixed `CoderAgent.execute` to correctly respect pre-approved tool resumes instead of discarding active tool states.
- **Approval Handshake Loop**: Addressed Orchestrator shell resumption stalling by introducing execution bypass markers that prevent circular re-approval prompts.
- **SQLAlchemy Greenlet/Pool Deadlock**: Patched test isolation by skipping database lock acquisitions within asynchronous runner threads during tool execution.

## [0.12.0] - 2026-05-28: GITEA ACTIONS CI/CD HEALER PIPELINE INTEGRATION
### Added
- **Gitea Actions CI/CD Healer Polling**: Replaced simulated/placeholder pipeline healing logic in `ci_healer.py` with a real `httpx.AsyncClient` client polling `/api/v1/repos/{owner}/{repo}/actions/runs`.
- **Platform Agnostic Environment-Based Configuration**: Integrated Gitea config parameters (`GITEA_BASE_URL`, `GITEA_TOKEN`, `GITEA_OWNER`, `GITEA_REPO`) using standard, portable environment variables rather than polluting the core platform's settings schema, strictly adhering to settings integrity guidelines.
- **SQLite Task Queueing**: Upgraded `initiate_healing` to query the SQLite task graph using `create_task()` to register an `orchestrator` task in `TaskStatus.PENDING` status.
- **Robustness Tests**: Implemented comprehensive unit tests in `tests/test_ci_healer.py` asserting correct polling, API interaction, double-processing prevention, and SQLite task scheduling.

## [0.11.1] - 2026-05-27: PRODUCTION DE-MOCKING: PREDICTIVE MAINTENANCE & BROWSER EXTRACTOR
### Fixed
- **PredictiveMaintenance Real Indexer**: `trigger_maintenance_task` previously slept for 10 seconds as a placeholder. Now delegates to `MemoryWorker._full_index()` — the real sema-throttled (10-concurrent) parallel indexer — keeping ChromaDB/RAG synchronized with actual workspace churn. Gracefully no-ops when ChromaDB is unavailable.
- **Browser `get_content` HTML→Text**: `browser_get_content` previously dumped raw HTML truncated at 2 000 characters. Now uses `page.inner_text("body")` for clean rendered-text extraction (no tag bleed-through), with a 10 000-character budget. Zero new dependencies — Playwright was already required.

## [0.11.0] - 2026-05-27: UNIVERSAL AUTOMATED TESTING & WASM/WASI VERIFICATION

### Added
- **Universal Testing Architecture & 100% Coverage**: Built an end-to-end integration and smoke testing suite across all three subsystems: Playwright browser E2E flows (Monaco hovers/jumps, MCP sandboxing matrix, Debate courtroom steerage), Rust Axum daemon routes, and Python backend P2P mesh discoverability and Security Sentinel audits.
- **WASM/WASI Native Run Verification**: Designed dynamic Wasmtime sandbox pipeline capturing stdout/stderr bytes in memory pipes, with automatic WAT-to-Wasm compilations and full verification tests.
- **Auto-Format on Save**: Standardized developer workflow by injecting `.vscode/settings.json` configuring default formatters (Rust, Python, TS/JS, JSON, CSS) and `editor.formatOnSave` enabled out of the box.

## [0.10.0] - 2026-05-26: BACKLOG PILLARS & PRODUCTION HARDENING
### Added
- **Local Screenplay Teleplay Replay Canvas**: Wired a high-fidelity chronological replay canvas to visualize and scrub agent decision beating and reasoning trajectories inside the Flight Log panel.
- **Dynamic Autonomy Level Transition**: Standardized and unified the `staging` autonomy level across the backend `AutonomyLevel` enum and dynamic CustomSelect triggers in the AI Panel and Settings panel, enabling real-time workspace sync via Zustand store actions.


## [0.9.0] - 2026-05-24: P2P MESH SYNC, SWARM MEMORY SUBSTRATE & SECURE CAPABILITY GUARDRAILS
### Added
- **P2P Mesh Workspace Sync**: Developed bi-directional directory synchronization over secure LAN mTLS. Implemented manifest validation, SHA-256 integrity checks, path traversal mitigation, and preservation of modification times.
- **Swarm Memory Substrate (Hive Mind)**: Exposed raw vector search across collective memory ChromaDB collections, implemented `refreshHiveStats` store statistics actions, and built a premium glassmorphic `SubstratePanel` dashboard in the UI.
- **Secure Human-in-the-Loop Guardrails**: Intercepted privileged `shell` and `filesystem` tool invocations under limited autonomy. Automatically halts executions, raises `approval_required` WebSocket event payloads, and prompts developers via an interactive glassmorphic modal to "Allow Once" or "Deny" execution.
- **Flawless Quality Gates**: Passed 100% of all 49/49 backend pytest cases, 0 pyright typecheck errors, and 0 eslint / ruff style check violations.

## [0.8.1] - 2026-05-24: HIGH-FIDELITY SECURITY HARDENING
### Added
- **High-Fidelity CodeQL Security Hardening**: Systematically resolved all remaining High and Critical CodeQL security alerts. Enforced standard, robust `os.path.realpath` startswith prefix matching for path traversal protection across 9 files (including `/tree`, `/read`, `/save`, `/upload`, `/create-folder`, `/delete` in files router, git workspace validation, AST coordinate boundaries, lsp_router, lsp_manager session init, scratchpad context, and skill subpath copy tree).
- **Polynomial REDoS Backtracking Protection**: Refactored the regular expression in `base_agent.py` to share the extension suffix group, completely neutralizing polynomial REDoS vulnerability when parsing markdown block fences.
- **Fast-Track Quality Verification**: Successfully achieved 100% clean pre-release gates with 49/49 passing backend unit tests, zero pyright typecheck errors, and zero ruff/eslint violations.

## [0.8.0] - 2026-05-23: EXTENSIBLE PLUGIN HUB & CODEBASE HYGIENE
### Added
- **Pillar A: Extensible Plugin Hub & Local Marketplace**: Implemented dynamic Plugin Hub endpoints (`GET /api/skills/marketplace` and `POST /api/skills/publish`) in the backend, backed by local mock storage (`.marketplace_mock.json`). Fully validated duplicate prevention, conflict assertions, and permission-gated developer roles.
- **Pillar B: Unified Discovery Canvas & Installed Badges**: Wired up the premium frontend "Discover" catalog to fetch directly from the marketplace unified API, featuring individual loading trackers ("Installing...") and green neon status badges for already-installed capabilities.
- **Pillar C: Rigorous Codebase Sanitization & Hygiene**: Permanently purged the orphaned legacy `SubstrateDashboard` panel directory. Conducted a comprehensive audit of the voice synthesis endpoints in `AIPanel.tsx`, gracefully routing them to the native browser speech fallback interface to completely eliminate speculative dead routes.
- **Pillar D: High-Fidelity Pre-Release Gates**: Hardened the entire development loop, achieving 100% green test passing rates across 49+ tests with strictly zero linter, formatter, typecheck, or runtime warnings/errors.

## [0.7.0] - 2026-05-22: GROUNDED INTELLIGENCE & DEVELOPER EXPERIENCE
### Added
- **Pillar A: Clean CI/CD & Teardown Hygiene**: Hardened pytest teardown hooks by cleanly shutting down `watcher_service` and disposing of SQLAlchemy connection pools on lifespan exit, achieving 100% clean pre-release gates with zero connection leaks, unhandled thread exceptions, or warnings.
- **Pillar B: Multi-Agent Consensus Debates**: Implemented a SQLite-backed persistent `DebateSession` state machine, a round-robin sequencer for multi-agent arguments, and a premium, highly responsive glassmorphic Courtroom UI with debate steering capabilities, real-time presence markers, and visualization dashboards.
- **Pillar C: Hermetic E2E WebSocket & Smoke Evaluations**: Added 6 new high-coverage E2E integration test scenarios to the smoke evaluation suite (`run_evals.py` and `test_smoke_evals.py`), fully verifying round-robin execution, concurrent WebSocket lock contention, and message streaming.

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
