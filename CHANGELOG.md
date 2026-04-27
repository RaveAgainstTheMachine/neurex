# Changelog

All notable changes to the Neurex project will be documented in this file.

## [v0.7.6-beta] - 2026-04-27

### Added
- **UI Stabilization**: Implemented a robust, state-driven resize handle system using native `react-resizable-panels` attributes (`data-resize-handle-state`).
- **Premium Aesthetics**: Added a layered violet glow effect (`--glow-purple`) to panel dividers on hover and drag.
- **Enhanced Visibility**: Combined the 6px hit-area with a 2px high-contrast core line to ensure interaction zones are unmistakable and premium.

### Fixed
- **Cursor Lock**: Resolved a regression where the cursor would get "permanently stuck" in a resize state after interacting with the bottom panel.
- **Cursor Style**: Replaced the "fist" (`grabbing`) cursor with the standard 4-point star (`move`) for all panel dividers.
- **Style Specificity**: Cleaned up overlapping CSS selectors in `App.css` to prevent flickering and inconsistent state rendering.

---

## [v0.7.5-beta] - 2026-04-26

### Added
- **Federated Governance**: Implemented DB-backed file locking and WebSocket-based presence broadcasting to prevent concurrent agent/user edit collisions.
- **Design System Tokens**: Defined `--purple-main` and `--glow-purple` in `index.css` as core branding variables.
