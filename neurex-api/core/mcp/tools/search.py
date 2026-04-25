"""
core/mcp/tools/search.py
High-performance search tools for codebase exploration.
"""
from __future__ import annotations
import os
import asyncio
import structlog
from pathlib import Path

log = structlog.get_logger()
WORKSPACE_ROOT = Path(os.getenv("WORKSPACE_PATH", "/workspace")).resolve()

async def grep_search(query: str, include_globs: list[str] | None = None) -> str:
    """
    Search for a literal string across the workspace using ripgrep.
    """
    log.info("mcp.grep_search.start", query=query)
    
    # Check if rg is installed
    import shutil
    rg_path = shutil.which("rg")
    
    cmd = ["rg", "--column", "--line-number", "--no-heading", "--color", "never", "--smart-case"]
    
    if include_globs:
        for glob in include_globs:
            cmd.extend(["-g", glob])
            
    cmd.append(query)
    cmd.append(str(WORKSPACE_ROOT))
    
    try:
        if rg_path:
            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            stdout, stderr = await process.communicate()
            
            if process.returncode != 0 and not stdout:
                if stderr:
                    log.error("mcp.grep_search.error", error=stderr.decode())
                    return f"Error: {stderr.decode()}"
                return f"No matches found for '{query}'."
                
            output = stdout.decode(errors="replace")
        else:
            # Fallback to slow python search if rg is missing
            log.warning("mcp.grep_search.no_rg_found")
            matches = []
            for root, _, files in os.walk(WORKSPACE_ROOT):
                for file in files:
                    if file.startswith("."): continue
                    path = Path(root) / file
                    try:
                        with open(path, "r", errors="replace") as f:
                            for i, line in enumerate(f, 1):
                                if query.lower() in line.lower():
                                    matches.append(f"{path.relative_to(WORKSPACE_ROOT)}:{i}: {line.strip()}")
                                    if len(matches) > 100: break
                    except Exception:
                        continue
                    if len(matches) > 100: break
                if len(matches) > 100: break
            output = "\n".join(matches) if matches else f"No matches found for '{query}'."

        # Limit output
        lines = output.splitlines()
        if len(lines) > 200:
            output = "\n".join(lines[:200]) + f"\n... [truncated, {len(lines)-200} more matches]"
            
        log.info("mcp.grep_search.done", query=query, match_count=len(lines))
        return output
        
    except Exception as e:
        log.error("mcp.grep_search.failed", error=str(e))
        return f"Error: {str(e)}"
