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
TRASH_ROOT = Path(os.getenv("NEUREX_TRASH_PATH", str(WORKSPACE_ROOT / ".neurex" / "trash"))).resolve()

def _safe_path(relative_path: str) -> Path:
    """Resolve and validate that the path stays within WORKSPACE_ROOT and NOT in TRASH_ROOT."""
    # Ensure workspace root exists
    if not WORKSPACE_ROOT.exists():
        WORKSPACE_ROOT.mkdir(parents=True, exist_ok=True)

    try:
        # Join and resolve
        resolved = (WORKSPACE_ROOT / relative_path).resolve()
        
        # Security check: must be inside WORKSPACE_ROOT
        if not resolved.is_relative_to(WORKSPACE_ROOT):
            raise PermissionError(
                f"Path traversal attempt blocked: {relative_path!r} "
                f"resolves outside workspace."
            )
            
        # Rogue agent safeguard: Block access to trash
        if resolved.is_relative_to(TRASH_ROOT):
             raise PermissionError(
                f"Access denied: {relative_path!r} is inside the protected Trash directory. "
                "Agents are not permitted to read, write, or delete files from the trash."
            )
            
        return resolved
    except (ValueError, RuntimeError) as e:
        raise PermissionError(f"Invalid path {relative_path!r}: {e}")


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


async def write_file(path: str, content: str, autonomy_level: str = "limited") -> str:
    """Write text content to a file in the workspace."""
    resolved = _safe_path(path)
    
    level = autonomy_level.lower()
    if level == "restricted":
        return f"APPROVAL_REQUIRED: Restricted mode: File write to '{path}' requires approval."

    from api.routes.files import collab_manager
    if not collab_manager.acquire_lock(path, "autonomous_agent_1"):
        return "Error: Collision detected. File is locked by another user. Retry later."
        
    try:
        resolved.parent.mkdir(parents=True, exist_ok=True)
        async with aiofiles.open(resolved, "w") as f:
            await f.write(content)
        log.info("fs.write", path=path, chars=len(content))
        return f"OK: wrote {len(content)} chars to {path}"
    finally:
        collab_manager.release_lock(path, "autonomous_agent_1")


async def delete_file(path: str, autonomy_level: str = "limited") -> str:
    """
    Soft-delete: moves to .neurex/trash/ instead of hard deleting.
    Ensures that misbehaving agents cannot permanently destroy data.
    """
    level = autonomy_level.lower()
    if level == "restricted":
        return f"APPROVAL_REQUIRED: Restricted mode: File deletion of '{path}' requires approval."

    resolved = _safe_path(path)
    if not resolved.exists():
        return f"Error: {path} does not exist"
        
    TRASH_ROOT.mkdir(parents=True, exist_ok=True)
    
    import shutil
    from datetime import datetime
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    trash_path = TRASH_ROOT / f"{timestamp}_{resolved.name}"
    
    shutil.move(str(resolved), str(trash_path))
    log.info("fs.soft_delete", path=path, trash=str(trash_path))
    return f"OK: {path} moved to trash as {trash_path.name}"


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


async def apply_diff(path: str, search: str, replace: str, autonomy_level: str = "limited") -> str:
    """
    Surgical edit: search for specific text and replace it.
    Both blocks must match whitespace exactly.
    """
    level = autonomy_level.lower()
    if level == "restricted":
        return f"APPROVAL_REQUIRED: Restricted mode: Applying diff to '{path}' requires approval."

    safe = _safe_path(path)
    if not safe.is_file():
        return f"Error: file not found: {path}"
    
    async with aiofiles.open(safe, "r", errors="replace") as f:
        content = await f.read()
    
    if search not in content:
        return (
            f"Error: exact search block not found in {path}. "
            f"Ensure whitespace, indentation, and characters match 100%."
        )
    
    # Check for multiple occurrences
    count = content.count(search)
    if count > 1:
        return (
            f"Error: multiple occurrences ({count}) of search block found in {path}. "
            f"Please provide a more unique context block."
        )
    
    new_content = content.replace(search, replace)
    async with aiofiles.open(safe, "w") as f:
        await f.write(new_content)
    
    log.info("fs.diff_applied", path=path, occurrences=count)
    return f"OK: applied diff to {path}."
