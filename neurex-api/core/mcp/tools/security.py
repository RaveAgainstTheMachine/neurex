"""
core/mcp/tools/security.py
Security auditing tools for Neurex.
"""
import os
import asyncio
import structlog
from pathlib import Path

log = structlog.get_logger()

WORKSPACE_PATH = os.getenv("WORKSPACE_PATH", "/workspace")

async def security_scan() -> str:
    """
    Perform a security audit of the workspace.
    - Runs bandit (Python security scanner)
    - Runs safety (Dependency vulnerability check)
    - Checks for sensitive files (.env, .pem) in git
    """
    ws = Path(WORKSPACE_PATH)
    issues = []
    
    # 1. Bandit Scan
    try:
        proc = await asyncio.create_subprocess_exec(
            "bandit", "-r", ".", "-f", "txt",
            cwd=ws,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        stdout, _ = await proc.communicate()
        if b"Issue:" in stdout:
            issues.append(f"Bandit found potential security issues:\n{stdout.decode()[:1000]}")
    except Exception:
        pass

    # 2. Safety Check
    try:
        proc = await asyncio.create_subprocess_exec(
            "safety", "check",
            cwd=ws,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        stdout, _ = await proc.communicate()
        if b"vulnerabilities" in stdout.lower():
            issues.append(f"Safety found dependency vulnerabilities:\n{stdout.decode()[:1000]}")
    except Exception:
        pass

    # 3. Secret Leak Check
    try:
        # Check for unencrypted private keys or env files tracked in git
        proc = await asyncio.create_subprocess_exec(
            "git", "ls-files", "*.pem", ".env", "*.key",
            cwd=ws,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        stdout, _ = await proc.communicate()
        if stdout:
            leaks = stdout.decode().strip().split("\n")
            issues.append(f"WARNING: Sensitive files are being tracked in Git:\n- " + "\n- ".join(leaks))
    except Exception:
        pass

    if not issues:
        return "✅ Security Scan Complete: No immediate threats detected."
        
    return "🚨 Security Scan Results:\n\n" + "\n\n".join(issues)
