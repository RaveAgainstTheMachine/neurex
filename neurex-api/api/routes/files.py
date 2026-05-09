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
class WorkspaceState:
    def __init__(self):
        self.config_path = Path.home() / ".neurex_last_workspace"
        self.path = None
        
        # Priority: Env Var > Saved State > None
        env_path = os.getenv("WORKSPACE_PATH")
        if env_path:
            self.path = Path(env_path).resolve()
        elif self.config_path.exists():
            try:
                saved = self.config_path.read_text().strip()
                if saved == "NONE":
                    self.path = None
                elif saved and Path(saved).exists():
                    self.path = Path(saved).resolve()
            except (OSError, ValueError):
                pass

    def persist(self):
        try:
            val = str(self.path) if self.path else "NONE"
            self.config_path.write_text(val)
        except OSError:
            pass

workspace_state = WorkspaceState()

def get_workspace(requested_root: str = None) -> Path:
    if requested_root:
        p = Path(requested_root).resolve()
        if p.exists() and p.is_dir():
            return p
    if not workspace_state.path:
        return None
    return workspace_state.path

IGNORED = {".git", "node_modules", "__pycache__", ".neurex_trash"}

@router.get("/workspace")
async def get_workspace_info():
    """Get current workspace info."""
    if not workspace_state.path:
        return {"path": None, "name": None}
    return {
        "path": str(workspace_state.path),
        "name": workspace_state.path.name
    }

class WorkspaceRequest(BaseModel):
    path: str

@router.post("/workspace")
async def set_workspace(req: WorkspaceRequest):
    """Switch to a different workspace folder."""
    from core.logger import log
    if not req.path:
        workspace_state.path = None
        workspace_state.persist()
        return {"path": None, "status": "closed"}

    new_path = Path(req.path).resolve()
    if not new_path.exists() or not new_path.is_dir():
        raise HTTPException(status_code=400, detail="Invalid workspace path")
    
    log.info("files.workspace_switch", old=str(workspace_state.path), new=str(new_path))
    workspace_state.path = new_path
    workspace_state.persist()
    
    from core.settings.manager import settings_manager
    settings_manager.reload()
    
    # Notify other services if needed (e.g. MemoryWorker)
    # For now, we return and the frontend will refresh
    return {"path": str(new_path), "status": "switched"}

collab_manager = CollaborationManager()


@router.get("/tree")
async def file_tree(path: str = ".", depth: int = 2, root_path: str = None):
    from core.logger import log
    WORKSPACE = get_workspace(root_path)
    if not WORKSPACE:
        return {"name": "No Workspace", "type": "dir", "children": []}
    log.info("files.tree_request", path=path, depth=depth, workspace=str(WORKSPACE))
    target_path = (WORKSPACE / path).resolve()
    if not str(target_path).startswith(str(WORKSPACE)):
        raise HTTPException(status_code=403, detail="Path traversal blocked")
    git_status = {}
    try:
        from .git import get_all_git_roots
        git_roots = get_all_git_roots(WORKSPACE)
        for root in git_roots:
            res = subprocess.run(
                ["git", "status", "--porcelain"], 
                cwd=root, capture_output=True, text=True, timeout=2
            )
            for line in res.stdout.splitlines():
                if len(line) > 3:
                    status_codes = line[:2].strip()
                    path = line[3:].strip()
                    
                    # Handle renames
                    if "R" in status_codes and " -> " in path:
                        path = path.split(" -> ")[1].strip()
                    
                    # Relativize to workspace root
                    abs_path = (root / path).resolve()
                    try:
                        rel_to_workspace = str(abs_path.relative_to(WORKSPACE))
                        git_status[rel_to_workspace] = "M" if "M" in status_codes else "U" if "??" in status_codes else None
                    except ValueError:
                        pass
    except Exception as e:
        log.error("files.git_status_failed", error=str(e))
        pass
    from core.languages.lsp_manager import diagnostic_tracker
    
    def _walk(current_path: Path, current_depth: int) -> dict:
        try:
            rel_path = str(current_path.relative_to(WORKSPACE))
            if rel_path == ".": rel_path = ""
        except ValueError: rel_path = current_path.name
        name = current_path.name
        
        if current_path.is_dir():
            # Check if this directory or anything inside it has git status
            dir_has_m = False
            dir_has_u = False
            
            # Normalize rel_path for prefix matching
            prefix = rel_path + "/" if rel_path else ""
            
            for p, s in git_status.items():
                if p == rel_path or p.startswith(prefix):
                    if s == "M": dir_has_m = True
                    if s == "U": dir_has_u = True
                if dir_has_m and dir_has_u: break

            if current_depth <= 0:
                return {
                    "name": name, "type": "dir", "path": rel_path, 
                    "has_children": True,
                    "has_m": dir_has_m, "has_u": dir_has_u,
                    "errors": diagnostic_tracker.get_count_for_prefix(rel_path)
                }
            children = []
            total_errors = 0
            from core.settings.manager import settings_manager
            show_hidden = settings_manager.get("show_hidden_files")
            try:
                for entry in os.scandir(current_path):
                    if entry.name in IGNORED:
                        continue
                    if not show_hidden and entry.name.startswith("."):
                        continue
                        
                    child = _walk(Path(entry.path), current_depth - 1)
                    children.append(child)
                children.sort(key=lambda x: (x["type"] != "dir", x["name"].lower()))
            except PermissionError: pass
            return {
                "name": name, "type": "dir", "path": rel_path, 
                "children": children, 
                "has_m": dir_has_m, "has_u": dir_has_u,
                "errors": diagnostic_tracker.get_count_for_prefix(rel_path)
            }
        
        file_errors = len(diagnostic_tracker.get_for_path(rel_path))
        return {
            "name": name, "type": "file", "path": rel_path, 
            "status": git_status.get(rel_path),
            "errors": file_errors
        }
    if not target_path.exists(): return {"name": "root", "type": "dir", "children": [], "error": "Path not found"}
    return _walk(target_path, depth)

@router.get("/read")
async def read_file(path: str, root_path: str = None):
    """Read a workspace file by relative path."""
    WORKSPACE = get_workspace(root_path)
    if not WORKSPACE:
        raise HTTPException(status_code=400, detail="No workspace open")
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
    root_path: str = None
    requester_id: str = "anonymous"

@router.post("/save")
async def save_file(req: SaveRequest):
    """Write content to a workspace file."""
    WORKSPACE = get_workspace(req.root_path)
    if not WORKSPACE:
        raise HTTPException(status_code=400, detail="No workspace open")
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
    WORKSPACE = get_workspace()
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
    exclude_glob: str = "",
    root_path: str = ""
):
    """Global search in workspace using ripgrep or grep."""
    if not query:
        return []
        
    WORKSPACE = get_workspace(root_path)
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
                except (json.JSONDecodeError, KeyError):
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
                        except ValueError:
                            continue
            return matches[:200]
        except Exception as e:
            return {"error": str(e)}

@router.post("/replace-all")
async def replace_all(
    query: str,
    replacement: str,
    case_sensitive: bool = False,
    use_regex: bool = False,
    whole_word: bool = False,
    include_glob: str = "",
    exclude_glob: str = "",
    root_path: str = ""
):
    """Global search and replace in workspace."""
    WORKSPACE = get_workspace(root_path)
    
    # Use search_files logic to find matches first
    matches = await search_files(
        query=query,
        case_sensitive=case_sensitive,
        use_regex=use_regex,
        whole_word=whole_word,
        include_glob=include_glob,
        exclude_glob=exclude_glob,
        root_path=root_path
    )
    
    if not isinstance(matches, list) or not matches:
        return {"status": "ok", "replaced_count": 0}
        
    # Group by file
    file_matches = {}
    for m in matches:
        p = m["path"]
        if p not in file_matches:
            file_matches[p] = []
        file_matches[p].append(m)
        
    replaced_count = 0
    import re
    
    flags = 0 if case_sensitive else re.IGNORECASE
    if not use_regex:
        pattern = re.escape(query)
    else:
        pattern = query
        
    if whole_word:
        pattern = rf"\b{pattern}\b"
        
    try:
        prog = re.compile(pattern, flags)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Invalid regex: {str(e)}")
    
    for rel_path in file_matches:
        abs_path = (WORKSPACE / rel_path).resolve()
        if not abs_path.exists():
            continue
            
        try:
            content = abs_path.read_text(encoding="utf-8")
            new_content, count = prog.subn(replacement, content)
            if count > 0:
                abs_path.write_text(new_content, encoding="utf-8")
                replaced_count += count
        except Exception as e:
            log.error("files.replace_failed", path=rel_path, error=str(e))
            
    return {"status": "ok", "replaced_count": replaced_count}

class RenameRequest(BaseModel):
    old_path: str
    new_path: str
    root_path: str = None

@router.post("/rename")
async def rename_file(req: RenameRequest):
    """Rename or move a file/directory."""
    WORKSPACE = get_workspace(req.root_path)
    old_resolved = (WORKSPACE / req.old_path).resolve()
    new_resolved = (WORKSPACE / req.new_path).resolve()
    
    if not str(old_resolved).startswith(str(WORKSPACE)) or not str(new_resolved).startswith(str(WORKSPACE)):
        raise HTTPException(status_code=403, detail="Path traversal blocked")
        
    if not old_resolved.exists():
        raise HTTPException(status_code=404, detail="Source not found")
        
    if new_resolved.exists():
        raise HTTPException(status_code=409, detail="Destination already exists")
        
    old_resolved.rename(new_resolved)
    return {"old_path": req.old_path, "new_path": req.new_path, "status": "renamed"}

@router.post("/create-folder")
async def create_folder(path: str, root_path: str = None):
    """Create a new directory recursively."""
    WORKSPACE = get_workspace(root_path)
    resolved = (WORKSPACE / path).resolve()
    if not str(resolved).startswith(str(WORKSPACE)):
        raise HTTPException(status_code=403, detail="Path traversal blocked")
    resolved.mkdir(parents=True, exist_ok=True)
    return {"path": path, "status": "created"}

@router.delete("/delete")
async def delete_file(path: str, root_path: str = None):
    """Delete a file or directory recursively."""
    WORKSPACE = get_workspace(root_path)
    resolved = (WORKSPACE / path).resolve()
    
    if not str(resolved).startswith(str(WORKSPACE)):
        raise HTTPException(status_code=403, detail="Path traversal blocked")
        
    if not resolved.exists():
        raise HTTPException(status_code=404, detail="Path not found")
        
    if resolved.is_dir():
        shutil.rmtree(resolved)
    else:
        resolved.unlink()
        
    return {"path": path, "status": "deleted"}

@router.get("/browse")
async def browse_directories(path: str = "."):
    """List subdirectories for the folder picker."""
    import os
    from pathlib import Path
    # Since this is a router, we use the local get_workspace
    WORKSPACE = get_workspace()
    
    try:
        # If path is absolute, use it. If no workspace, default to home.
        target = Path(path)
        if not target.is_absolute():
            base = WORKSPACE if WORKSPACE else Path.home()
            target = (base / path).resolve()
        else:
            target = target.resolve()
            
        if not target.exists() or not target.is_dir():
            return {"dirs": [], "current": str(target), "error": "Not a directory"}
            
        dirs = []
        for entry in os.scandir(target):
            if entry.is_dir() and entry.name not in IGNORED:
                dirs.append(entry.name)
        dirs.sort()
        
        return {
            "dirs": dirs,
            "current": str(target),
            "parent": str(target.parent) if target.parent != target else None
        }
    except Exception as e:
        return {"dirs": [], "current": path, "error": str(e)}
