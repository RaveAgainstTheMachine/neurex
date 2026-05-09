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

async def run_command(command: str, cwd: str = ".", approved: bool = False, autonomy_level: str = "limited", mutation_allowed: bool = False) -> str:
    """
    Execute `command` inside a Docker sandbox container.
    If the command is unsafe and not pre-approved, returns an approval request.
    """
    level = autonomy_level.lower()
    trash_path = os.getenv("NEUREX_TRASH_PATH", ".neurex/trash")
    
    if trash_path in command:
         return f"ERROR: Access denied. Shell commands are not permitted to target the protected Trash directory: {trash_path}"

    if not approved:
        reason = None
        if level == "restricted":
            reason = "Restricted mode: All shell commands require approval."
        elif level == "limited" and not _check_safety(command):
            reason = f"Limited mode: Command '{command}' is potentially unsafe."
        elif mutation_allowed and level != "full":
            reason = "Mutation mode: Command requires write access to the workspace. Approval required."
            
        if reason:
            return f"APPROVAL_REQUIRED: {reason}"

    _check_allowlist(command)

    network_mode = "bridge" if os.getenv("ENABLE_AGENT_INTERNET", "false").lower() == "true" else "none"
    mount_mode = "rw" if mutation_allowed else "ro"

    docker_cmd = [
        "docker", "run", "--rm",
        "--network", network_mode,          # controlled internet access
        "--memory", "512m",
        "--cpus", "1",
        "-v", f"{WORKSPACE_PATH}:/workspace:{mount_mode}",
        "-w", f"/workspace/{cwd.lstrip('/')}",
        SANDBOX_IMAGE,
        "sh", "-c", command,
    ]

    log.info("terminal.exec", command=command, cwd=cwd, mode=mount_mode)

    try:
        proc = await asyncio.create_subprocess_exec(
            *docker_cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.STDOUT,
        )
        try:
            stdout, _ = await asyncio.wait_for(proc.communicate(), timeout=TIMEOUT)
        except TimeoutError:
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
        # Docker not available, try WASM fallback
        log.warning("terminal.docker_not_found", error="Docker not detected. Attempting WASM/WASI fallback...")
        try:
            return await _wasm_exec_fallback(command, cwd)
        except Exception as e:
            log.error("terminal.wasm_fallback_failed", error=str(e))
            if os.getenv("NEUREX_ALLOW_HOST_FALLBACK", "false").lower() == "true":
                log.warning("terminal.host_fallback_active", warning="UNSAFE: Running on host!")
                return await _host_exec_fallback(command, cwd)
            
            return f"Error: Docker not found and WASM fallback failed ({e}). Sandboxed execution is mandatory. Please start Docker or ensure neurex-cli is running."

async def _wasm_exec_fallback(command: str, cwd: str) -> str:
    """Securely execute via the Rust CLI's Sandbox Engine (WASM or Native Fallback)."""
    import httpx
    
    cli_url = os.getenv("NEUREX_CLI_URL", "http://localhost:3000")
    wasm_path = os.path.expanduser("~/.neurex/bin/coreutils.wasm")
    
    # Payload always includes args, wasm_path is optional
    payload = {
        "args": ["sh", "-c", command] if os.path.exists(wasm_path) else command.split()
    }
    
    if os.path.exists(wasm_path):
        payload["wasm_path"] = wasm_path
        log.info("terminal.wasm_exec", command=command)
    else:
        log.info("terminal.native_fallback_exec", command=command, reason="wasm_tooling_missing")

    async with httpx.AsyncClient(timeout=60.0) as client:
        resp = await client.post(f"{cli_url}/api/sandbox/exec", json=payload)
        if resp.status_code != 200:
            raise Exception(f"Sandbox Host error: {resp.text}")
        
        data = resp.json()
        stdout = data.get("stdout", "")
        stderr = data.get("stderr", "")
        rc = data.get("exit_code", -1)
        error = data.get("error")

        if error:
            return f"❌ Sandbox Engine Error: {error}"

        output = stdout + stderr
        status = "✅ exit 0" if rc == 0 else f"❌ exit {rc}"
        prefix = "[WASM]" if "wasm_path" in payload else "[NATIVE]"
        return f"{prefix} {status}\n{output}"

async def _host_exec_fallback(command: str, cwd: str) -> str:
    """UNSAFE: Directly execute on host. Requires NEUREX_ALLOW_HOST_FALLBACK=true"""
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
    except TimeoutError:
        proc.kill()
        return f"Error: timed out after {TIMEOUT}s"

    output = stdout.decode(errors="replace")
    rc = proc.returncode
    return f"[HOST EXEC - UNSAFE] exit {rc}\n{output}"
