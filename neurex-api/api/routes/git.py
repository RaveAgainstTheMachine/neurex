# neurex-api/api/routes/git.py
from fastapi import APIRouter, Depends, HTTPException, Query
from typing import List, Optional
import subprocess
import os

from .auth import get_current_user
# subprocess-based git management

router = APIRouter(prefix="/api/git", tags=["git"])

def run_git(args: List[str]):
    try:
        res = subprocess.run(["git"] + args, capture_output=True, text=True, check=True)
        return res.stdout.strip()
    except subprocess.CalledProcessError as e:
        raise HTTPException(status_code=500, detail=f"Git error: {e.stderr}")

@router.get("/status")
async def get_status(user=Depends(get_current_user)):
    try:
        branch = run_git(["rev-parse", "--abbrev-ref", "HEAD"])
        status_raw = run_git(["status", "--porcelain"])
        
        changes = []
        if status_raw:
            for line in status_raw.split("\n"):
                if not line: continue
                # XY path
                status_codes = line[:2]
                path = line[3:]
                
                # Simplified status mapping
                status = "modified"
                if "A" in status_codes: status = "added"
                if "D" in status_codes: status = "deleted"
                if "?" in status_codes: status = "untracked"
                
                # Staged if first char is not space
                staged = status_codes[0] != " " and status_codes[0] != "?"
                
                changes.append({
                    "path": path,
                    "status": status,
                    "staged": staged
                })
                
        return {"branch": branch, "changes": changes}
    except Exception as e:
        return {"branch": "unknown", "changes": []}

@router.post("/stage")
async def stage_file(payload: dict, user=Depends(get_current_user)):
    run_git(["add", payload["path"]])
    return {"status": "ok"}

@router.post("/unstage")
async def unstage_file(payload: dict, user=Depends(get_current_user)):
    run_git(["reset", "HEAD", payload["path"]])
    return {"status": "ok"}

@router.get("/diff")
async def get_diff(path: str = Query(...), user=Depends(get_current_user)):
    try:
        # Get original from HEAD
        original = ""
        try:
            original = run_git(["show", f"HEAD:{path}"])
        except:
            pass # File might be new
            
        # Get current from disk
        with open(path, "r") as f:
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
