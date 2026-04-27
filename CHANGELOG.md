# Changelog

All notable changes to the Neurex project will be documented in this file.

## [v0.8.3-beta] - 2026-04-27

### Added
- **Intelligent Mesh Balancing**: Refactored `MeshRouter` to use a uniform scoring algorithm for local and peer nodes. Introduced a 5% jitter tier to prevent "dogpiling" and ensure balanced load distribution across the federated mesh.
- **Distributed MPI Discovery (Phase 10.5)**: Finalized the `llama.cpp` RPC master/worker handshake. The system now dynamically aggregates compute nodes from both real-time presence and the persistent mesh peer registry when launching distributed inference.
- **In-Depth Infra Status**: Enhanced `/api/infra/status` to report real-time RPC worker metrics and endpoints.

### Fixed
- **WebSocket Resilience**: Implemented more aggressive "zombie" connection sweeping (10s intervals) and reduced timeout to 25s to improve presence accuracy during micro-disconnects.

---

## [v0.8.2-beta] - 2026-04-27

### Added
- **Open Source Only Policy**: Formally purged all BYOK (Bring Your Own Key) integrations for closed-source models (OpenAI, Anthropic, Gemini). Neurex is now exclusively powered by open-source weights.
- **Model Specialty Tags**: Refactored the AI Panel (InfraPanel) to display specialty tags like `(coding)`, `(thinking)`, and `(vision)` in the Agent Recommendations section, improving UI readability.

### Fixed
- **UI Interaction**: Resolved a bug where panel borders were reacting to mouse movement while models were open.
- **Store Consistency**: Unified `API_BASE` and improved auth state cleanup.

---

## [v0.8.1-beta] - 2026-04-27

### Fixed
- **Infra Hub**: Background borders no longer react to hover when model modal is open.
- **Search Panel**: Query and results now persist across navigation and refreshes via localStorage.

## [v0.8.0-beta] - 2026-04-27

### Added
- **Advanced Search Panel**: Re-implemented the Search Activity Bar tab with `ripgrep` (`rg`) integration.
  - Added support for Case Sensitivity, Regex, and Whole Word toggles.
  - Implemented Glob-based include/exclude filtering.
  - High-density result rendering with code snippets and line numbers.
- **Memory Worker Resilience**: Improved the background indexing service to gracefully handle outages of external services (Ollama, ChromaDB).
- **Backend Cleanup**: Optimized `files.py` imports and set dynamic `WORKSPACE_PATH` defaults for local development.

### Fixed
- **Database Schema**: Fixed a bug where the `chatmessage` table was not initialized during project startup.

---

## [v0.7.6-beta] - 2026-04-27

### Added
- **Federated Governance**: Implemented DB-backed file locking and WebSocket-based presence broadcasting to prevent concurrent agent/user edit collisions.
- **Design System Tokens**: Defined `--purple-main` and `--glow-purple` in `index.css` as core branding variables.
