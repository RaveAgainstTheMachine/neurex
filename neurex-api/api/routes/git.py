# neurex-api/api/routes/git.py
import os
import subprocess
from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException, Query

from .auth import get_current_user
from .files import get_workspace

# subprocess-based git management

router = APIRouter()


def _validate_safe_path(path: str) -> Path:
    workspace = get_workspace()
    if not workspace:
        raise HTTPException(status_code=400, detail="No workspace open")
    
    safe_root = os.path.realpath(str(workspace))
    target = os.path.realpath(os.path.join(safe_root, path))
    safe_prefix = safe_root if safe_root.endswith(os.sep) else safe_root + os.sep
    
    if not target.startswith(safe_prefix) and target != safe_root:
        raise HTTPException(status_code=403, detail="Path traversal blocked")
        
    return Path(target)



def run_git(args: list[str], cwd: str | None = None):
    workspace = get_workspace()
    if not cwd:
        cwd = str(workspace)

    try:
        # SECURITY: Subprocess is used with a list of arguments (shell=False), which is safe
        # from shell injection. For parameter injection, callers should use '--' where needed.
        res = subprocess.run(["git"] + args, capture_output=True, text=True, check=True, cwd=cwd)
        return res.stdout.strip()
    except subprocess.CalledProcessError as e:
        raise HTTPException(status_code=500, detail=f"Git error: {e.stderr}")


def get_all_git_roots(workspace: Path) -> list[Path]:
    """Find all directories containing a .git folder within the workspace."""
    roots = []
    # Check workspace itself
    if (workspace / ".git").is_dir():
        roots.append(workspace)

    # Scan subdirectories (shallow scan for performance, but deep enough for common patterns)
    try:
        # We use a limited depth find to avoid performance issues in massive node_modules etc
        res = subprocess.run(
            ["find", ".", "-maxdepth", "4", "-name", ".git", "-type", "d"],
            cwd=workspace,
            capture_output=True,
            text=True,
            timeout=5,
        )
        for line in res.stdout.splitlines():
            if line:
                # remove /.git and convert to absolute
                root = (workspace / line).parent.resolve()
                if root not in roots:
                    roots.append(root)
    except (subprocess.SubprocessError, OSError):
        pass
    return roots


@router.get("/status")
async def get_status(user=Depends(get_current_user)):
    try:
        workspace = get_workspace()
        git_roots = get_all_git_roots(workspace)

        all_changes = []
        main_branch = "unknown"

        for root in git_roots:
            try:
                # Get branch for this root
                branch = subprocess.run(
                    ["git", "rev-parse", "--abbrev-ref", "HEAD"],
                    cwd=root,
                    capture_output=True,
                    text=True,
                    check=True,
                ).stdout.strip()

                if root == workspace or main_branch == "unknown":
                    main_branch = branch

                # Get status for this root
                status_raw = subprocess.run(
                    ["git", "status", "--porcelain"],
                    cwd=root,
                    capture_output=True,
                    text=True,
                    check=True,
                ).stdout.strip()

                if status_raw:
                    for line in status_raw.split("\n"):
                        if not line:
                            continue
                        status_codes = line[:2]
                        path = line[3:].strip()

                        # Handle renames (R  old -> new)
                        if "R" in status_codes and " -> " in path:
                            path = path.split(" -> ")[1].strip()

                        # Resolve path relative to workspace root
                        abs_path = (root / path).resolve()
                        try:
                            rel_to_workspace = str(abs_path.relative_to(workspace))
                        except ValueError:
                            rel_to_workspace = path  # Fallback

                        # Simplified status mapping
                        status = "modified"
                        if "A" in status_codes:
                            status = "added"
                        if "D" in status_codes:
                            status = "deleted"
                        if "?" in status_codes:
                            status = "untracked"

                        # Staged if first char is not space
                        staged = status_codes[0] != " " and status_codes[0] != "?"

                        all_changes.append(
                            {
                                "path": rel_to_workspace,
                                "status": status,
                                "staged": staged,
                                "repo_root": str(root),
                            }
                        )
            except (subprocess.CalledProcessError, OSError):
                continue

        return {"branch": main_branch, "changes": all_changes}
    except Exception:
        return {"branch": "unknown", "changes": []}


@router.post("/stage")
async def stage_file(payload: dict, user=Depends(get_current_user)):
    resolved = _validate_safe_path(payload["path"])
    rel_path = str(resolved.relative_to(get_workspace()))
    run_git(["add", "--", rel_path])
    return {"status": "ok"}


@router.post("/unstage")
async def unstage_file(payload: dict, user=Depends(get_current_user)):
    resolved = _validate_safe_path(payload["path"])
    rel_path = str(resolved.relative_to(get_workspace()))
    run_git(["reset", "HEAD", "--", rel_path])
    return {"status": "ok"}


@router.get("/diff")
async def get_diff(path: str = Query(...), user=Depends(get_current_user)):
    try:
        workspace = get_workspace()
        resolved = _validate_safe_path(path)
        rel_path = str(resolved.relative_to(workspace))

        # Get original from HEAD
        original = ""
        try:
            original = run_git(["show", f"HEAD:{rel_path}"])
        except HTTPException:
            pass  # File might be new

        # Get current from disk
        with open(resolved) as f:
            modified = f.read()

        return {"original": original, "modified": modified}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/commit")
async def commit_changes(payload: dict, user=Depends(get_current_user)):
    run_git(["commit", "-m", payload["message"]])
    return {"status": "ok"}


@router.post("/generate_commit_msg")
async def generate_commit_msg(user=Depends(get_current_user)):
    # Simple logic for now: get diff and summarize
    diff = run_git(["diff", "--cached", "--stat"])
    if not diff:
        return {"message": "Small cleanups and documentation updates"}

    # In a real scenario, we would pass 'diff' to an LLM here.
    # For now, we'll return a semantic placeholder or a basic summary.
    return {"message": f"feat: update system components\n\nChanges identified:\n{diff}"}


@router.get("/blame")
async def get_blame(path: str = Query(...), user=Depends(get_current_user)):
    try:
        resolved = _validate_safe_path(path)
        rel_path = str(resolved.relative_to(get_workspace()))
        # Use line-porcelain for detailed, stable parsing
        res = run_git(["blame", "--line-porcelain", "--", rel_path])
        lines = []
        current_blame = {}

        for line in res.split("\n"):
            if not line:
                continue
            if len(line) >= 40 and " " not in line[:40]:  # SHA line
                current_blame = {"hash": line[:8]}
            elif line.startswith("author "):
                current_blame["author"] = line[7:]
            elif line.startswith("author-time "):
                current_blame["time"] = int(line[12:])
            elif line.startswith("summary "):
                current_blame["summary"] = line[8:]
            elif line.startswith("\t"):
                # Line content marks the end of a porcelain block
                lines.append(current_blame.copy())
        return {"blame": lines}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/history")
async def get_history(path: str = Query(...), user=Depends(get_current_user)):
    try:
        resolved = _validate_safe_path(path)
        rel_path = str(resolved.relative_to(get_workspace()))
        # Get history with hash, author, time, and summary
        res = run_git(["log", "--pretty=format:%h|%an|%at|%s", "--", rel_path])
        history = []
        if res:
            for line in res.split("\n"):
                if not line:
                    continue
                parts = line.split("|", 3)
                if len(parts) == 4:
                    h, a, t, s = parts
                    history.append({"hash": h, "author": a, "time": int(t), "summary": s})
        return {"history": history}
    except Exception:
        return {"history": []}
