# Security & Authentication

Neurex implements a **Zero-Trust Role-Based Access Control (RBAC)** system designed for secure collaborative development.

## 1. Authentication Layer
- **JWT Mandatory**: Every API request must carry a Bearer JWT.
- **Strict Configuration**: The API will refuse to start if the `JWT_SECRET` environment variable is not set.

## 2. Invitation System (Onboarding)
To prevent unauthorized public access, Neurex uses a **Time-Limited Invite System**.
- **Admin Control**: Only `admin` users can generate invite codes via `POST /api/auth/invite/create`.
- **Registration**: New users must provide a valid, unused `invite_code` to the `/register` endpoint.

## 3. RBAC Hierarchy
- **Admin**: Full infrastructure control, user management, and mesh topology access.
- **Developer**: Full read/write access to workspace, skill installation, and agent execution.
- **Viewer**: Read-only access to files and logs.

## 4. Hardened Security
- **Path Sanitization**: All skill installations via Git are strictly sanitized to prevent **Path Traversal** attacks. `..` and absolute paths are forbidden in sub-path definitions.
- **Shell Sandbox**: Agents execute shell commands in a restricted environment with PTY-level monitoring.
