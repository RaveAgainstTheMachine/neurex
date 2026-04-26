"""api/routes/files.py — Workspace file browser endpoints."""
import os
from pathlib import Path
from fastapi import APIRouter, HTTPException, UploadFile, File
from pydantic import BaseModel
import shutil
import subprocess
import ast
from core.collaboration.manager import CollaborationManager

router = APIRouter()
WORKSPACE = Path(os.getenv("WORKSPACE_PATH", "/workspace"))
IGNORED = {".git", "node_modules", "__pycache__", ".neurex_trash"}

collab_manager = CollaborationManager()


@router.get("/tree")
async def file_tree():
    """Return a nested JSON file tree of the workspace with Git status."""
    # Fetch Git Status
    git_status = {}
    try:
        res = subprocess.run(
            ["git", "status", "--porcelain"], 
            cwd=WORKSPACE, capture_output=True, text=True, check=True
        )
        for line in res.stdout.splitlines():
            if len(line) > 3:
                status = line[:2].strip()
                path = line[3:].strip()
                # Status: M (Modified), ?? (Untracked) -> U
                git_status[path] = "M" if "M" in status else "U" if "??" in status else None
    except:
        pass

    def _get_file_errors(path: Path) -> int:
        """Heuristic check for critical syntax errors."""
        if path.suffix == ".py":
            try:
                ast.parse(path.read_text(errors="ignore"))
                return 0
            except:
                return 1
        return 0

    def _walk(path: Path) -> dict:
        name = path.name
        rel_path = str(path.relative_to(WORKSPACE))
        
        if path.is_dir():
            children = []
            items = sorted(path.iterdir(), key=lambda p: (not p.is_dir(), p.name.lower()))
            for child in items:
                if child.name not in IGNORED:
                    children.append(_walk(child))
            return {"name": name, "type": "dir", "children": children}
        
        return {
            "name": name, 
            "type": "file", 
            "path": rel_path,
            "status": git_status.get(rel_path),
            "errors": _get_file_errors(path)
        }

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
class SaveRequest(BaseModel):
    path: str
    content: str
    requester_id: str = "anonymous"

@router.post("/save")
async def save_file(req: SaveRequest):
    """Write content to a workspace file."""
    resolved = (WORKSPACE / req.path).resolve()
    if not str(resolved).startswith(str(WORKSPACE)):
        raise HTTPException(status_code=403, detail="Path traversal blocked")
    
    # Advanced Collision Prevention
    if not collab_manager.acquire_lock(req.path, req.requester_id):
        raise HTTPException(status_code=423, detail=f"File is currently locked by another user or agent.")
    
    try:
        # Ensure parent directory exists
        resolved.parent.mkdir(parents=True, exist_ok=True)
        resolved.write_text(req.content)
    finally:
        # Release lock immediately after successful write
        collab_manager.release_lock(req.path, req.requester_id)
        
    return {"path": req.path, "status": "saved"}

@router.post("/upload")
async def upload_file(file: UploadFile = File(...), path: str = "uploads"):
    """Upload a file to the workspace."""
    # Ensure relative path
    clean_path = path.lstrip("/")
    resolved_dir = (WORKSPACE / clean_path).resolve()
    
    if not str(resolved_dir).startswith(str(WORKSPACE)):
        raise HTTPException(status_code=403, detail="Path traversal blocked")
        
    resolved_dir.mkdir(parents=True, exist_ok=True)
    file_path = resolved_dir / file.filename
    
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
        
    return {"filename": file.filename, "path": str(file_path.relative_to(WORKSPACE)), "status": "uploaded"}

import subprocess

@router.get("/search")
async def search_files(query: str):
    """Global grep search in workspace."""
    if not query:
        return []
        
    try:
        # Run grep -rnI (recursive, line number, ignore binary)
        result = subprocess.run(
            ["grep", "-rnI", query, str(WORKSPACE)],
            capture_output=True,
            text=True,
            timeout=10
        )
        
        matches = []
        for line in result.stdout.splitlines():
            if ":" in line:
                parts = line.split(":", 2)
                if len(parts) >= 3:
                    full_path, line_num, content = parts
                    rel_path = str(Path(full_path).relative_to(WORKSPACE))
                    matches.append({
                        "path": rel_path,
                        "line": int(line_num),
                        "content": content.strip()
                    })
        return matches[:200]  # Limit to 200 results
    except Exception as e:
        return {"error": str(e)}
