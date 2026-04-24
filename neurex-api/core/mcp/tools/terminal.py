"""
core/mcp/tools/terminal.py
Sandboxed command execution via Docker. Commands run inside an isolated
container with the workspace mounted read-only by default.

Security model:
  - No network access in the sandbox container
  - Workspace mounted read-only (test runner sees files but cannot write)
  - Hard timeout (60s) prevents runaway processes
  - Command allowlist enforced before exec
"""
from __future__ import annotations
import asyncio
import os
import shlex
import structlog

log = structlog.get_logger()

WORKSPACE_PATH = os.getenv("WORKSPACE_PATH", "/workspace")
SANDBOX_IMAGE  = os.getenv("SANDBOX_IMAGE", "neurex-sandbox:latest")
TIMEOUT        = 60  # seconds

# Only these top-level commands are permitted in the sandbox
ALLOWED_COMMANDS = {
    "pytest", "python", "python3", "ruff", "mypy", "black",
    "eslint", "prettier", "tsc", "jest", "vitest", "npm",
    "pnpm", "yarn", "cargo", "go", "rustfmt", "cat", "ls",
    "find", "grep", "wc", "echo",
}


SAFE_COMMANDS = {
    "ls", "cat", "pwd", "git status", "git diff", "pytest", "npm test",
}

def _check_allowlist(command: str) -> None:
    parts = shlex.split(command)
    if not parts:
        raise PermissionError("Empty command.")
    binary = os.path.basename(parts[0])
    if binary not in ALLOWED_COMMANDS:
        raise PermissionError(
            f"Command '{binary}' is not in the sandbox allowlist. "
            f"Allowed: {', '.join(sorted(ALLOWED_COMMANDS))}"
        )

def _check_safety(command: str) -> bool:

    """Returns True if the command is completely safe and doesn't need approval."""
    parts = shlex.split(command)
    if not parts: return True
    binary = os.path.basename(parts[0])
    # Very restrictive safe-list
    return binary in {"ls", "pwd", "git"} and "rm" not in command and "mv" not in command

async def run_command(command: str, cwd: str = ".", approved: bool = False) -> str:
    """
    Execute `command` inside a Docker sandbox container.
    If the command is unsafe and not pre-approved, returns an approval request.
    """
    if not approved and not _check_safety(command):
        return f"APPROVAL_REQUIRED: The command '{command}' is marked as potentially unsafe. Please approve or deny."

    _check_allowlist(command)


    docker_cmd = [
        "docker", "run", "--rm",
        "--network", "none",          # no internet access
        "--memory", "512m",
        "--cpus", "1",
        "-v", f"{WORKSPACE_PATH}:/workspace:ro",
        "-w", f"/workspace/{cwd.lstrip('/')}",
        SANDBOX_IMAGE,
        "sh", "-c", command,
    ]

    log.info("terminal.exec", command=command, cwd=cwd)

    try:
        proc = await asyncio.create_subprocess_exec(
            *docker_cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.STDOUT,
        )
        try:
            stdout, _ = await asyncio.wait_for(proc.communicate(), timeout=TIMEOUT)
        except asyncio.TimeoutError:
            proc.kill()
            return f"Error: command timed out after {TIMEOUT}s"

        output = stdout.decode(errors="replace")
        rc = proc.returncode

        # Truncate huge outputs
        if len(output) > 20_000:
            output = output[:20_000] + "\n... [output truncated]"

        status = "✅ exit 0" if rc == 0 else f"❌ exit {rc}"
        return f"{status}\n{output}"

    except FileNotFoundError:
        # Docker not available — fall back to direct host exec (dev only)
        log.warning("terminal.docker_not_found", fallback="host_exec")
        return await _host_exec_fallback(command, cwd)


async def _host_exec_fallback(command: str, cwd: str) -> str:
    """
    DEV ONLY fallback when Docker is not available.
    Runs directly on the host — never use in production.
    """
    import os
    workspace = os.getenv("WORKSPACE_PATH", "/workspace")
    work_dir  = os.path.join(workspace, cwd.lstrip("/"))

    proc = await asyncio.create_subprocess_shell(
        command,
        cwd=work_dir,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.STDOUT,
    )
    try:
        stdout, _ = await asyncio.wait_for(proc.communicate(), timeout=TIMEOUT)
    except asyncio.TimeoutError:
        proc.kill()
        return f"Error: timed out after {TIMEOUT}s"

    output = stdout.decode(errors="replace")
    rc = proc.returncode
    return f"[HOST EXEC - DEV ONLY] exit {rc}\n{output}"
