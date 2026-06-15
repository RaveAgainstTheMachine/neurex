# Known Issues & Technical Debt

This document serves as an honest inventory of Neurex's current technical debt, security gaps, and unvalidated claims. If you are considering running Neurex, especially in a networked environment, you must read this first.

## Zero Test Coverage Modules

The following 16 core modules have **0% test coverage**. They have never been formally validated and should be considered experimental.

| Module | Path | Risk |
| :--- | :--- | :--- |
| FederatedRAG | `core/context/federated_rag.py` | Untested distributed retrieval |
| NeuralExplorer | `core/context/neural_explorer.py` | Untested codebase navigation |
| SkepticalMemory | `core/context/skeptical_memory.py` | Untested fact verification |
| MeshIntel | `core/mcp/tools/mesh_intel.py` | Untested mesh tooling |
| NeuralHarness | `core/mcp/servers/neural_harness.py` | Untested inference wrapper |
| CommanderAgent | `core/agents/commander_agent.py` | Untested agent orchestration |
| ReviewerAgent | `core/agents/reviewer_agent.py` | Untested code review agent |
| DependencyAgent | `core/agents/dependency_agent.py` | Untested dependency management |
| Insomnia | `core/infrastructure/insomnia.py` | Untested keep-alive |
| LoggingMiddleware | `core/infrastructure/logging_middleware.py` | Untested request logging |
| Maintenance | `core/infrastructure/maintenance.py` | Untested maintenance mode |
| SkillsHarvester | `core/skills/harvester.py` | Untested skill discovery |
| HiveManager | `core/collaboration/hive_manager.py` | Untested collaboration layer |
| Somnus | `core/harness/somnus.py` | Untested sleep/wake management |
| CertManager | `core/security/certs.py` | Untested TLS certificate handling |
| Logger | `core/logger.py` | Untested structured logging setup |

## Known Security Issues

**CRITICAL**: Core modules still require external human audit before deployment in untrusted environments. See [SECURITY_AUDIT.md](./SECURITY_AUDIT.md) for more details.

## Honest Status

- **Zero outside users** have ever run this software.
- All "stable" and "production-ready" claims historically made in this repository were based exclusively on automated tests written by AI agents.
- The **Plugin Hub** and **Marketplace** are entirely mocked stubs. They do not function.
- **P2P Mesh Sync** is simulated only. It has never been tested against real multi-device scenarios.
