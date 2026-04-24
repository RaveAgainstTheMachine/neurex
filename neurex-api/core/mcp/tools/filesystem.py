"""
core/mcp/tools/filesystem.py
Filesystem tools scoped to WORKSPACE_PATH. All paths are resolved relative
to the workspace root and validated to prevent path traversal.
"""
from __future__ import annotations
import os
from pathlib import Path
import aiofiles
import structlog

log = structlog.get_logger()

WORKSPACE_ROOT = Path(os.getenv("WORKSPACE_PATH", "/workspace")).resolve()


def _safe_path(relative_path: str) -> Path:
    """Resolve and validate that the path stays within WORKSPACE_ROOT."""
    resolved = (WORKSPACE_ROOT / relative_path).resolve()
    if not str(resolved).startswith(str(WORKSPACE_ROOT)):
        raise PermissionError(
            f"Path traversal attempt blocked: {relative_path!r} "
            f"resolves outside workspace."
        )
    return resolved


async def read_file(path: str) -> str:
    safe = _safe_path(path)
    if not safe.is_file():
        return f"Error: file not found: {path}"
    async with aiofiles.open(safe, "r", errors="replace") as f:
        content = await f.read()
    # Truncate very large files to avoid flooding context
    if len(content) > 40_000:
        content = content[:40_000] + f"\n... [truncated at 40k chars]"
    log.info("fs.read", path=path, chars=len(content))
    return content


async def write_file(path: str, content: str) -> str:
    safe = _safe_path(path)
    safe.parent.mkdir(parents=True, exist_ok=True)
    async with aiofiles.open(safe, "w") as f:
        await f.write(content)
    log.info("fs.write", path=path, chars=len(content))
    return f"OK: wrote {len(content)} chars to {path}"


async def list_directory(path: str = ".") -> str:
    safe = _safe_path(path)
    if not safe.is_dir():
        return f"Error: not a directory: {path}"
    entries = []
    for item in sorted(safe.iterdir()):
        rel = item.relative_to(WORKSPACE_ROOT)
        kind = "dir" if item.is_dir() else "file"
        entries.append(f"{kind}  {rel}")
    return "\n".join(entries) if entries else "(empty directory)"


async def delete_file(path: str) -> str:
    """
    Soft-delete: moves to .neurex_trash/ instead of hard deleting.
    This prevents irreversible destruction by a misbehaving agent.
    """
    safe = _safe_path(path)
    if not safe.exists():
        return f"Error: path not found: {path}"
    trash = WORKSPACE_ROOT / ".neurex_trash"
    trash.mkdir(exist_ok=True)
    dest = trash / safe.relative_to(WORKSPACE_ROOT)
    dest.parent.mkdir(parents=True, exist_ok=True)
    safe.rename(dest)
    log.info("fs.soft_delete", path=path, trash=str(dest))
    return f"OK: moved {path} to .neurex_trash/"
