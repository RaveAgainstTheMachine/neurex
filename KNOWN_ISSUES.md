# Known Issues & Technical Debt

This document serves as an honest inventory of Neurex's current technical debt, security gaps, and unvalidated claims. If you are considering running Neurex, especially in a networked environment, you must read this first.

## Zero Test Coverage Modules

All 16 core modules previously listed here have been covered with unit and integration tests under `neurex-api/tests/`.


## Known Security Issues

**CRITICAL**: Core modules still require external human audit before deployment in untrusted environments. See [SECURITY_AUDIT.md](./SECURITY_AUDIT.md) for more details.

## Honest Status

- **Zero outside users** have ever run this software.
- All "stable" and "production-ready" claims historically made in this repository were based exclusively on automated tests written by AI agents.
- The **Plugin Hub** and **Marketplace** are entirely mocked stubs. They do not function.
- **P2P Mesh Sync** is simulated only. It has never been tested against real multi-device scenarios.
