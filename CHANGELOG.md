# Changelog

All notable changes to the Neurex project will be documented in this file.

## [v0.8.8-beta] - 2026-04-27

### Added
- **Language Mode Overrides**: Added a manual language selector to the editor status bar, allowing users to override automatic extension detection.
- **Enhanced Activity Bar**: 
  - Implemented notification badges for active agent tasks and system events.
  - Added "Active Tab" indicators (vertical bar + glow) for better spatial orientation.
- **Elite File Icons**: Integrated a comprehensive icon set for the File Explorer, covering modern tech stacks (Vite, Docker, React, Python venvs).
- **Tab Meta-State**: Added "Dirty" markers and file icons to the editor tabs to improve multi-file navigation.

### Fixed
- **Explorer Density**: Improved the layout density and spacing of the File Explorer for a more professional IDE feel.
- **Monaco Polish**: Enabled bracket pair colorization and automatic layout adjustments in the EditorPane.

---

## [v0.8.7-beta] - 2026-04-27

### Added
- **Native HTML Preloader**: Injected a high-performance CSS/HTML preloader into `index.html`. This provides an **instant** (0ms delay) visual feedback loop the moment the page is requested, completely eliminating the "black screen" during JavaScript bundle parsing.
- **Global Initialization State**: Migrated the `isInitialized` state from local component memory to the global Zustand store. This ensures the app only initializes once per session, preventing the "reloading bar" loop during auth state changes.

### Fixed
- **Hook Structural Integrity**: Performed a full architectural rewrite of `App.tsx` to resolve React Hook violations (nested `useEffect` calls). All lifecycle hooks are now correctly positioned at the top level.
- **Deadlock-Proof Startup**: Refactored `refreshInfra()` and workspace initialization to be non-blocking. Non-critical infrastructure metrics no longer stall the IDE boot process, and direct state mutations were replaced with reactive store actions.
- **Auth-Aware Handoff**: Implemented a secondary `useEffect` to force-hide the preloader if no session token is detected, ensuring the login screen is immediately visible to logged-out users.
