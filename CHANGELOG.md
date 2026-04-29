# Changelog

All notable changes to the Neurex project will be documented in this file.

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

## [0.1.2] - 2026-04-28
### Added
- **Dynamic Theme Engine**: implemented `color-mix` based design tokens, allowing the entire UI (including chat) to reactively adapt to the user's primary accent color.
- **Immediate Settings Preview**: configuration changes now apply in real-time to the DOM before persistence.
- **Batch State Management**: introduced `handleBatchChange` in `SettingsPanel` to eliminate state race conditions during rapid property updates.

### Fixed
- **Settings Persistence**: resolved a critical bug where non-admin users were blocked from saving visual preferences due to the presence of restricted infrastructure keys in the payload.
- **RBAC Hardening**: refined the backend settings validator to only enforce admin-only checks if the restricted key's value is actually modified.
- **Color Sync**: standardized all default colors to HEX format to ensure 1:1 synchronization with native browser color pickers.
- **Terminal Anchor**: reconfigured xterm.js layout to anchor the active cursor to the bottom of the container, eliminating visual gaps and ensuring input stability during scroll-down events.
- **Chat UI**: applied primary accent colors to user message bubbles and thinking animations for full thematic unity.

## [0.1.1] - 2026-04-28
### Added
- Initial IDE Core implementation.
- Monaco Editor integration.
- WebSocket-based Mesh Network heartbeat.
- HSL-based Design System and Glassmorphism.
