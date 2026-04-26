from __future__ import annotations
import os
import asyncio
import structlog
from pathlib import Path

log = structlog.get_logger()
WORKSPACE_ROOT = Path(os.getenv("WORKSPACE_PATH", "/workspace")).resolve()

async def grep_search(query: str, include_globs: list[str] | None = None) -> str:
    log.info("mcp.grep_search.start", query=query)
    
    import shutil
    rg_path = shutil.which("rg")
    
    if not rg_path:
        return "ripgrep (rg) is not installed on the system."

    cmd = ["rg", "--column", "--line-number", "--no-heading", "--color", "never", "--smart-case"]
    
    if include_globs:
        for glob in include_globs:
            cmd.extend(["-g", glob])
            
    cmd.append(query)
    cmd.append(str(WORKSPACE_ROOT))
    
    try:
        proc = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        stdout, stderr = await proc.communicate()
        
        if stderr:
            log.error("mcp.grep_search.error", error=stderr.decode())
            
        return stdout.decode()
    except Exception as e:
        log.error("mcp.grep_search.failed", error=str(e))
        return f"Error executing search: {str(e)}"
