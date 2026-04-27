# Changelog

All notable changes to the Neurex project will be documented in this file.

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
