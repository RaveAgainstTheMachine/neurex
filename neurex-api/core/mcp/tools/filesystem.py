"""
core/mcp/tools/filesystem.py
Filesystem tools scoped to WORKSPACE_PATH. All paths are resolved relative
to the workspace root and validated to prevent path traversal.
"""

from __future__ import annotations

import contextvars
import os
from pathlib import Path

import aiofiles
import structlog

log = structlog.get_logger()

workspace_path_var: contextvars.ContextVar[str | None] = contextvars.ContextVar("workspace_path", default=None)


def get_workspace_root() -> Path:
    wp = workspace_path_var.get()
    if wp:
        return Path(wp).resolve()
    
    import sys
    if "pytest" not in sys.modules:
        config_path = Path.home() / ".neurex_last_workspace"
        if config_path.exists():
            try:
                saved = config_path.read_text().strip()
                if saved and saved != "NONE":
                    sp = Path(saved).resolve()
                    if sp.exists():
                        return sp
            except Exception:
                pass

    return Path(os.getenv("WORKSPACE_PATH", "/workspace")).resolve()


def get_trash_root() -> Path:
    return Path(
        os.getenv("NEUREX_TRASH_PATH", str(get_workspace_root() / ".neurex" / "trash"))
    ).resolve()


def get_staging_root() -> Path:
    return get_workspace_root() / ".neurex" / "staging"


def _safe_path(relative_path: str) -> Path:
    """Resolve and validate that the path stays within get_workspace_root() and NOT in get_trash_root()."""
    root = get_workspace_root()
    trash = get_trash_root()
    
    # Ensure workspace root exists
    if not root.exists():
        root.mkdir(parents=True, exist_ok=True)

    try:
        # Join and resolve
        resolved = (root / relative_path).resolve()

        # Security check: must be inside root
        if not resolved.is_relative_to(root):
            raise PermissionError(
                f"Path traversal attempt blocked: {relative_path!r} resolves outside workspace."
            )

        # Rogue agent safeguard: Block access to trash
        if resolved.is_relative_to(trash):
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
    async with aiofiles.open(safe, errors="replace") as f:
        content = await f.read()
    # Truncate very large files to avoid flooding context
    if len(content) > 40_000:
        content = content[:40_000] + "\n... [truncated at 40k chars]"
    log.info("fs.read", path=path, chars=len(content))
    return content


async def write_file(path: str, content: str, autonomy_level: str = "limited") -> str:
    """Write text content to a file in the workspace, supporting staging mode."""
    resolved = _safe_path(path)

    level = autonomy_level.lower()
    if level == "restricted":
        return f"APPROVAL_REQUIRED: Restricted mode: File write to '{path}' requires approval."

    target_path = resolved
    if level == "staging":
        rel = resolved.relative_to(get_workspace_root())
        target_path = get_staging_root() / rel

        # If the file had a deletion marker, remove it
        marker_path = get_staging_root() / f"{rel}.deleted"
        if marker_path.exists():
            marker_path.unlink()

    target_path.parent.mkdir(parents=True, exist_ok=True)
    async with aiofiles.open(target_path, "w") as f:
        await f.write(content)
    log.info("fs.write", path=path, chars=len(content), staged=(level == "staging"))
    return f"OK: wrote {len(content)} chars to {path}"


async def delete_file(path: str, autonomy_level: str = "limited") -> str:
    """
    Soft-delete: moves to .neurex/trash/ instead of hard deleting.
    Ensures that misbehaving agents cannot permanently destroy data.
    Supports staging mode by creating a .deleted marker file.
    """
    level = autonomy_level.lower()
    if level == "restricted":
        return f"APPROVAL_REQUIRED: Restricted mode: File deletion of '{path}' requires approval."

    resolved = _safe_path(path)
    if not resolved.exists():
        if level == "staging":
            rel = resolved.relative_to(get_workspace_root())
            staged_path = get_staging_root() / rel
            if not staged_path.exists():
                return f"Error: {path} does not exist"
        else:
            return f"Error: {path} does not exist"

    if level == "staging":
        rel = resolved.relative_to(get_workspace_root())
        target_path = get_staging_root() / rel
        # If it was already written in staging, delete it
        if target_path.is_file():
            target_path.unlink()

        # Write a deletion marker file
        marker_path = get_staging_root() / f"{rel}.deleted"
        marker_path.parent.mkdir(parents=True, exist_ok=True)
        async with aiofiles.open(marker_path, "w") as f:
            await f.write("DELETED")

        log.info("fs.stage_delete", path=path)
        return f"OK: staged deletion of {path}."

    get_trash_root().mkdir(parents=True, exist_ok=True)

    import shutil
    from datetime import datetime

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    trash_path = get_trash_root() / f"{timestamp}_{resolved.name}"

    shutil.move(str(resolved), str(trash_path))
    log.info("fs.soft_delete", path=path, trash=str(trash_path))
    return f"OK: {path} moved to trash as {trash_path.name}"


async def list_directory(path: str = ".") -> str:
    safe = _safe_path(path)
    if not safe.is_dir():
        return f"Error: not a directory: {path}"
    entries = []
    for item in sorted(safe.iterdir()):
        rel = item.relative_to(get_workspace_root())
        kind = "dir" if item.is_dir() else "file"
        entries.append(f"{kind}  {rel}")
    return "\n".join(entries) if entries else "(empty directory)"


async def apply_diff(path: str, search: str, replace: str, autonomy_level: str = "limited") -> str:
    """
    Surgical edit: search for specific text and replace it.
    Both blocks must match whitespace exactly.
    Supports staging mode by writing results to STAGING_ROOT.
    """
    level = autonomy_level.lower()
    if level == "restricted":
        return f"APPROVAL_REQUIRED: Restricted mode: Applying diff to '{path}' requires approval."

    safe = _safe_path(path)

    # Read from staging if it exists, otherwise from original
    source_path = safe
    if level == "staging":
        rel = safe.relative_to(get_workspace_root())
        staged_path = get_staging_root() / rel
        if staged_path.is_file():
            source_path = staged_path
        elif not safe.is_file():
            return f"Error: file not found: {path}"
    else:
        if not safe.is_file():
            return f"Error: file not found: {path}"

    async with aiofiles.open(source_path, errors="replace") as f:
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

    # Write to target
    target_path = safe
    if level == "staging":
        rel = safe.relative_to(get_workspace_root())
        target_path = get_staging_root() / rel
        target_path.parent.mkdir(parents=True, exist_ok=True)

        # If the file had a deletion marker, remove it
        marker_path = get_staging_root() / f"{rel}.deleted"
        if marker_path.exists():
            marker_path.unlink()

    async with aiofiles.open(target_path, "w") as f:
        await f.write(new_content)

    log.info("fs.diff_applied", path=path, occurrences=count, staged=(level == "staging"))
    return f"OK: applied diff to {path}."


async def list_staging() -> list[dict]:
    """List all files in staging, categorized as modified or deleted."""
    staging = get_staging_root()
    if not staging.exists():
        return []

    staged = []
    # Walk staging directory
    for root, _, files in os.walk(staging):
        for f in files:
            full_path = Path(root) / f
            rel = full_path.relative_to(staging)

            if f.endswith(".deleted"):
                # It's a deletion marker
                original_rel = str(rel)[:-8]  # Strip .deleted
                staged.append({"path": original_rel, "status": "deleted"})
            else:
                # Check if it was already listed as deleted (e.g. deletion markers exist)
                staged.append({"path": str(rel), "status": "modified"})
    return staged


async def clear_staging():
    """Clear all staged files."""
    staging = get_staging_root()
    if staging.exists():
        import shutil

        shutil.rmtree(staging)
        log.info("fs.staging_cleared")


async def commit_staging() -> dict:
    """Commit all staged modifications to WORKSPACE_ROOT."""
    staging = get_staging_root()
    workspace = get_workspace_root()
    if not staging.exists():
        return {"status": "ok", "committed_count": 0}

    staged_items = await list_staging()
    committed_count = 0

    import shutil

    for item in staged_items:
        rel_path = item["path"]
        staged_file = staging / rel_path
        original_file = workspace / rel_path

        if item["status"] == "deleted":
            # Delete original file
            if original_file.exists():
                if original_file.is_dir():
                    shutil.rmtree(original_file)
                else:
                    original_file.unlink()
                committed_count += 1
              # Clean up the marker file
            marker_file = staging / f"{rel_path}.deleted"
            if marker_file.exists():
                marker_file.unlink()
        else:
            # Copy modified/new file from staging to original
            if staged_file.is_file():
                original_file.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(staged_file, original_file)
                committed_count += 1

    # Now clear staging
    await clear_staging()
    log.info("fs.staging_committed", count=committed_count)
    return {"status": "ok", "committed_count": committed_count}
