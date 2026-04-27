"""api/routes/files.py — Workspace file browser endpoints."""
import os
import json
import shutil
import subprocess
from pathlib import Path
from fastapi import APIRouter, HTTPException, UploadFile, File
from pydantic import BaseModel
from core.collaboration.manager import CollaborationManager

router = APIRouter()
WORKSPACE = Path(os.getenv("WORKSPACE_PATH", os.getcwd()))
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
            cwd=WORKSPACE, capture_output=True, text=True, timeout=5
        )
        for line in res.stdout.splitlines():
            if len(line) > 3:
                status = line[:2].strip()
                path = line[3:].strip()
                git_status[path] = "M" if "M" in status else "U" if "??" in status else None
    except:
        pass

    def _walk(path: Path) -> dict:
        name = path.name
        try:
            rel_path = str(path.relative_to(WORKSPACE))
        except ValueError:
            rel_path = name
        
        if path.is_dir():
            children = []
            try:
                # Use os.scandir for better performance on large directories
                for entry in os.scandir(path):
                    if entry.name not in IGNORED:
                        children.append(_walk(Path(entry.path)))
                children.sort(key=lambda x: (x["type"] != "dir", x["name"].lower()))
            except PermissionError:
                pass
            return {"name": name, "type": "dir", "children": children}
        
        return {
            "name": name, 
            "type": "file", 
            "path": rel_path,
            "status": git_status.get(rel_path)
        }

    if not WORKSPACE.exists():
        return {"name": "root", "type": "dir", "children": [], "error": "Workspace not found"}
        
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
async def search_files(
    query: str, 
    case_sensitive: bool = False, 
    use_regex: bool = False, 
    whole_word: bool = False,
    include_glob: str = "",
    exclude_glob: str = ""
):
    """Global search in workspace using ripgrep or grep."""
    if not query:
        return []
        
    # Prefer ripgrep (rg) if available
    rg_path = shutil.which("rg")
    
    if rg_path:
        cmd = [rg_path, "--column", "--line-number", "--no-heading", "--color", "never", "--json"]
        
        if not case_sensitive:
            cmd.append("--ignore-case")
        if not use_regex:
            cmd.append("--fixed-strings")
        if whole_word:
            cmd.append("--word-regexp")
        
        if include_glob:
            for g in include_glob.split(","):
                cmd.extend(["--glob", g.strip()])
        if exclude_glob:
            for g in exclude_glob.split(","):
                cmd.extend(["--glob", f"!{g.strip()}"])
                
        cmd.append(query)
        cmd.append(str(WORKSPACE))
        
        try:
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
            matches = []
            
            # rg --json output is a stream of JSON objects per line
            for line in result.stdout.splitlines():
                try:
                    data = json.loads(line)
                    if data.get("type") == "match":
                        payload = data["data"]
                        full_path = payload["path"]["text"]
                        
                        # Handle absolute vs relative path resolution
                        try:
                            f_path = Path(full_path)
                            if f_path.is_absolute():
                                rel_path = str(f_path.relative_to(WORKSPACE))
                            else:
                                # rg with relative path
                                rel_path = full_path
                        except ValueError:
                            # Not under workspace, skip or use absolute
                            rel_path = full_path
                            
                        line_num = payload["line_number"]
                        content = payload["lines"]["text"]
                        matches.append({
                            "path": rel_path,
                            "line": line_num,
                            "content": content.strip()
                        })
                except:
                    continue
            return matches[:500]
        except Exception as e:
            return {"error": str(e)}
    else:
        # Fallback to grep
        cmd = ["grep", "-rnI"]
        if not case_sensitive:
            cmd.append("-i")
        if not use_regex:
            cmd.append("-F")
        if whole_word:
            cmd.append("-w")
            
        # Grep globbing is limited, we just use standard grep
        cmd.extend([query, str(WORKSPACE)])
        
        try:
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
            matches = []
            for line in result.stdout.splitlines():
                if ":" in line:
                    parts = line.split(":", 2)
                    if len(parts) >= 3:
                        full_path, line_num, content = parts
                        try:
                            rel_path = str(Path(full_path).relative_to(WORKSPACE))
                            matches.append({
                                "path": rel_path,
                                "line": int(line_num),
                                "content": content.strip()
                            })
                        except:
                            continue
            return matches[:200]
        except Exception as e:
            return {"error": str(e)}

