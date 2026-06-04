# Security Policy

## Supported Versions

Neurex is currently in active development. Only the latest version of the `main` branch is supported for security updates.

| Version | Supported          |
| ------- | ------------------ |
| v0.5.x  | :white_check_mark: |
| < v0.5  | :x:                |

## Reporting a Vulnerability

We take the security of Neurex seriously. If you believe you have found a security vulnerability, please do NOT open a public issue. Instead, please report it privately.

To report a vulnerability, please contact the maintainers via GitHub private messaging or the contact information provided in the repository profile.

When reporting a vulnerability, please include:
- A description of the vulnerability.
- Steps to reproduce the issue.
- Potential impact.

We will acknowledge receipt of your report within 48 hours and provide a timeline for resolution.

## Security Practices
- **Local Sovereignty**: Neurex is designed to run locally. We recommend never exposing the API or Web ports directly to the public internet without a secure reverse proxy like the provided Caddy configuration with mTLS enabled.
- **Sandboxing**: All agent-generated code should be executed within the provided Docker sandbox.
- **Secret Management**: Never commit `.env` files or private keys. Neurex is configured to ignore these by default.
- **Input Sanitization**: As of v0.5.3, Neurex strictly sanitizes all URL inputs for SSRF prevention, isolates file access to mitigate path traversal, and uses positional arguments (`--`) to prevent command injection across all subprocess layers.
