"""
core/mcp/tools/workspace.py
Maintenance tools for workspace integrity.
"""

import asyncio
import os
import shutil
from pathlib import Path

import structlog

log = structlog.get_logger()

WORKSPACE_PATH = os.getenv("WORKSPACE_PATH", "/workspace")


async def deep_clean() -> str:
    """
    Perform deep cleaning of the workspace.
    - Removes __pycache__, .pytest_cache, .mypy_cache
    - Runs git clean -fd (if git is available)
    - Runs ruff --fix (if ruff is available)
    """
    ws = Path(WORKSPACE_PATH)
    cleaned = []

    # 1. Purge Caches
    for cache_dir in [".pytest_cache", ".mypy_cache", ".ruff_cache", "__pycache__"]:
        for path in ws.rglob(cache_dir):
            try:
                if path.is_dir():
                    shutil.rmtree(path)
                else:
                    path.unlink()
                cleaned.append(str(path.relative_to(ws)))
            except Exception:
                continue

    # 2. Git Clean
    try:
        proc = await asyncio.create_subprocess_exec(
            "git",
            "clean",
            "-fd",
            cwd=ws,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        stdout, _ = await proc.communicate()
        if stdout:
            cleaned.append(f"Git cleaned: {stdout.decode().strip()}")
    except Exception:
        pass

    # 3. Ruff Fix
    try:
        proc = await asyncio.create_subprocess_exec(
            "ruff",
            "check",
            "--fix",
            ".",
            cwd=ws,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        await proc.communicate()
        cleaned.append("Applied ruff fixes")
    except Exception:
        pass

    if not cleaned:
        return "Workspace is already clean."

    return (
        "Deep Clean Complete:\n- "
        + "\n- ".join(cleaned[:20])
        + (f"\n... and {len(cleaned) - 20} more" if len(cleaned) > 20 else "")
    )


async def analyze_project_structure() -> str:
    """
    Generate a high-level summary of the project architecture and technology stack.
    """
    ws = Path(WORKSPACE_PATH)
    files = [f.name for f in ws.iterdir() if f.is_file()]
    dirs = [d.name for d in ws.iterdir() if d.is_dir() and not d.name.startswith(".")]

    summary = [f"Project Root: {ws.name}"]
    summary.append(f"Directories: {', '.join(dirs)}")

    # Tech Stack Detection
    stack = []
    if (ws / "package.json").exists():
        stack.append("Node.js/TypeScript")
    if (ws / "requirements.txt").exists() or (ws / "pyproject.toml").exists():
        stack.append("Python")
    if (ws / "Cargo.toml").exists():
        stack.append("Rust")
    if (ws / "go.mod").exists():
        stack.append("Go")
    if (ws / "Dockerfile").exists():
        stack.append("Docker")

    summary.append(f"Detected Stack: {', '.join(stack) if stack else 'Unknown'}")

    return "\n".join(summary)
