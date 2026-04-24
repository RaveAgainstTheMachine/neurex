"""api/routes/files.py — Workspace file browser endpoints."""
import os
from pathlib import Path
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

router = APIRouter()
WORKSPACE = Path(os.getenv("WORKSPACE_PATH", "/workspace"))
IGNORED = {".git", "node_modules", "__pycache__", ".neurex_trash"}


@router.get("/tree")
async def file_tree():
    """Return a nested JSON file tree of the workspace."""
    def _walk(path: Path) -> dict:
        name = path.name
        if path.is_dir():
            children = []
            for child in sorted(path.iterdir()):
                if child.name not in IGNORED:
                    children.append(_walk(child))
            return {"name": name, "type": "dir", "children": children}
        return {"name": name, "type": "file", "path": str(path.relative_to(WORKSPACE))}

    return _walk(WORKSPACE)


@router.get("/read")
async def read_file(path: str):
    """Read a workspace file by relative path."""
    resolved = (WORKSPACE / path).resolve()
    if not str(resolved).startswith(str(WORKSPACE)):
        raise HTTPException(status_code=403, detail="Path traversal blocked")
    if not resolved.is_file():
        raise HTTPException(status_code=404, detail="File not found")
    content = resolved.read_text(errors="replace")
    return {"path": path, "content": content}
