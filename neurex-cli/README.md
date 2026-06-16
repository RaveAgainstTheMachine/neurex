# Neurex CLI (Daemon)

The Neurex CLI is the unified entry point for the **Neurex Platform**. It is designed as a lightweight, native daemon (Rust) that handles the complex Dual-Layer architecture of the IDE.

## Dual-Layer Architecture
For security and performance, Neurex 1.0 operates across two boundaries:

1. **Control Plane (Host Layer)**: 
   The frontend (Vite/React) and the light telemetry proxy (FastAPI) run directly on the host machine. This ensures perfect file-watcher latency (`inotify`/`fsevents`), immediate UI responsiveness, and removes volume-binding friction for the user's workspace.
2. **Execution Plane (Sandboxed Layer)**: 
   The Autonomous Agents (`CoderAgent`, `LSP Linter`) and PTY execution terminals run exclusively inside a secure OS-level sandbox (Docker/Podman/bwrap). Agents cannot accidentally modify the host system outside of the explicitly mounted workspace directory.

## Commands

### `neurex start`
Bootstraps the platform.
- Detects host dependencies (Docker, GPU drivers).
- Spins up the local Control Plane.
- Mounts the current directory into an ephemeral Execution Sandbox.

### `neurex doctor`
Validates system readiness for [UNIMPLEMENTED] Phase 53.
- **Hardware Introspection**: Uses `sysinfo` to query the host OS, Kernel version, CPU architecture, and available RAM.
- **Container Validation**: Uses `bollard` to query the local Docker socket (`/var/run/docker.sock`) to ensure the execution sandbox engine is reachable.

### `neurex stop`
Gracefully drains and kills all isolated agent containers and stops the host control plane.

## Development
```bash
cargo run -- start
cargo run -- doctor
```
