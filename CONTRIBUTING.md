# Neurex Development & Contribution Guidelines

## 1. Zero-Trust & Skeptical Memory
Neurex enforces a **Zero-Trust** filesystem discipline. Before any mutation:
- **Verify State**: Use `grep_search` or `read_file` to confirm the current state of the file. Do not rely on context memory alone.
- **HyperPlan Pass**: All complex architectural changes must be vetted via the `hyperplan` tool (Decomposition -> Trace -> Optimization).
- **Swarm Consensus**: Major mutations require a 2/3 vote majority from the multi-agent debate loop (when `consensus_enabled=True`).

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

For the complete release cadence, batching rules, and Gitea/GitHub tag lifecycle, see [RELEASE_POLICY.md](./RELEASE_POLICY.md).

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

## 6. Testing & Quality Assurance (QA)
- **Unit Testing**: Run `make test` for rapid feedback on business logic. Use `make test-cov` to verify that your changes are covered.
- **Unmocked Integration Tests**: Neurex runs heavy daemons (Ollama, Firewall Managers, RPC meshes). To test these properly without clashing with the host machine, run `make test-integration`. This spins up the full FastAPI lifespan with unmocked daemons bound to safe randomized local ports.
- **CI/CD Constraints**: Integration tests execute locally, as GitHub Actions runners may lack the requisite GPU access or root permissions for firewall manipulation.

---
*Enshrined by the Neurex Core Team.*
