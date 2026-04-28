# Changelog

All notable changes to the Neurex project will be documented in this file.

## [Unreleased] - 2026-04-28 (CAVEMAN ULTRA UPDATE)

### Added
- **Global Command Palette (Cmd+Shift+P)**: Universal entry point for all IDE actions, including file management, view toggling, and developer tools.
- **Source Control (Git) Integration**: A dedicated sidebar panel for staging changes, viewing branch status, and committing code with keyboard shortcuts (Cmd+Enter).
- **Mature Search & Replace**:
  - Implemented result grouping by File (expandable/collapsible).
  - Added 'Replace All' functionality with regex support.
  - Added fuzzy search for results.
- **Burger Menu 2.0**: Unified the top-level menu into a single, branded '⬡' trigger in the Activity Bar.
- **Interactive Status Bar**: Real-time cursor position, indentation selection, encoding selection, and language mode switching via Command Palettes.
- **AI Intelligence Indicators**: Pulse animations for active AI composition and thinking states.

### Fixed
- **Infinite Layout Bleeding**: Enforced strict `min-width: 0` and `overflow: hidden` across the entire flex layout.
- **Terminal Rendering**: Achieved a 'flush' seamless look with synced background colors (#050507) and descender clearance (+2px lifting).
- **Redundant UI Elements**: Fused the Neurex logo with the menu trigger and removed redundant headers.
- **Empty Space Artifacts**: Fixed PanelGroup constraints to ensure edge-to-edge rendering of the AIPanel.

### Changed
- Refactored `App.tsx` into a lean, professional layout engine.
- Migrated all IDE actions to a unified `MenuBar` logic tree.
- Standardized tooltips across every interactive icon in the IDE.

## [0.1.0] - 2026-04-27
### Added
- Initial IDE Core implementation.
- Monaco Editor integration.
- WebSocket-based Mesh Network heartbeat.
- HSL-based Design System and Glassmorphism.
