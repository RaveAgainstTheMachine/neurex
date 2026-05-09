# Neurex Development & Contribution Guidelines

## 1. Zero-Trust & Skeptical Memory
Neurex enforces a **Zero-Trust** filesystem discipline. Before any mutation:
- **Verify State**: Use `grep_search` or `read_file` to confirm the current state of the file. Do not rely on context memory alone.
- **HyperPlan Pass**: All complex architectural changes must be vetted via the `hyperplan` tool (Decomposition -> Trace -> Optimization).
- **Swarm Consensus**: Major mutations require a 2/3 quorum approval from the Neural Swarm Consensus engine.

## 2. Regression Prevention
Before submitting any UI or Backend change, the following must be verified:
- **Build Integrity**: Run `npm run build` in the `neurex-web` directory to ensure no TypeScript or JSX syntax errors were introduced.
- **Service Status**: Ensure the backend API (`uvicorn`) is running and reachable.
- **Terminal Connectivity**: Verify that the PTY session remains active and persists through page refreshes.

## 3. Versioning & SemVer
Neurex follows [Semantic Versioning (SemVer)](https://semver.org/):
- **MAJOR**: Breaking changes that require infrastructure or DB migration.
- **MINOR**: New features (e.g., adding HyperPlan, Mesh RAG).
- **Atomic Commits**: Use descriptive, conventional commit messages (e.g., `feat:`, `fix:`, `docs:`).
- **Automated Validation**: Every push and Pull Request triggers the **Neurex CI** workflow. This runs:
  - `ruff` and `mypy` on the backend.
  - `npm run build` on the frontend.

## 📁 Repository Structure
All new UI components MUST respect the "Persistence Principle":
- Open files, active tabs, and terminal history must survive a browser refresh.
- Leverage `localStorage` for frontend state and the `PTYManager` for shell state.

## 4. Collaborative Ethics
- **Locks**: Always use the `CollaborationManager` when writing to files to prevent race conditions between users and agents.
- **Presence**: Broadcast cursor positions and active file changes via the `presence_update` WebSocket event.

## 5. Zero-Friction Development
- **Persistence First**: All new features must justify why they do NOT persist before being accepted. State is sacred.
- **Agentic Parity**: Code for humans is code for agents. Tool interfaces must be as clean as UI interfaces.
- **Documentation**: All architectural changes must be reflected in the [Roadmap](./ROADMAP.md).

---
*Enshrined by the Neurex Core Team.*
