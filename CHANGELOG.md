# Changelog

All notable changes to the Neurex project will be documented in this file.

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
