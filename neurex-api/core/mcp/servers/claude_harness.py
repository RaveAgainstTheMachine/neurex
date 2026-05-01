"""
core/mcp/servers/claude_harness.py
MCP server that wraps the Claude Code CLI in a secure Docker sandbox.
Allows Neurex to delegate complex, repo-wide tasks to Claude.
"""
from __future__ import annotations
import asyncio
import os
import structlog
from typing import Dict, Any

log = structlog.get_logger()

async def run_claude_harness(query: str, workspace_path: str | None = None) -> str:
    """
    Executes a query using the Claude Code harness inside a secure sandbox.
    """
    ws = workspace_path or os.getenv("WORKSPACE_PATH", "/workspace")
    log.info("claude_harness.invoked", query=query, workspace=ws)
    
    # 1. Build/Check Sandbox Image (Phase 28)
    # For now, we assume the image 'neurex-claude-sandbox:latest' is pre-built.
    
    # 2. Prepare Docker Command
    # We mount the workspace with RW permissions for Claude to act.
    # We pass the query as a command-line argument.
    cmd = [
        "docker", "run", "--rm",
        "-v", f"{ws}:/workspace",
        "-e", f"ANTHROPIC_API_KEY={os.getenv('ANTHROPIC_API_KEY')}",
        "neurex-claude-sandbox:latest",
        "--non-interactive",
        query
    ]
    
    try:
        process = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        
        stdout, stderr = await process.communicate()
        
        if process.returncode != 0:
            error_msg = stderr.decode().strip()
            log.error("claude_harness.failed", error=error_msg)
            return f"Claude Harness Error: {error_msg}"
            
        result = stdout.decode().strip()
        log.info("claude_harness.success", output_len=len(result))
        return result
        
    except Exception as e:
        log.critical("claude_harness.exception", error=str(e))
        return f"Critical failure in Claude Harness: {str(e)}"

# Registration logic for the MCP Client
TOOL_DEFINITION = {
    "name": "claude_harness",
    "description": "Delegates a complex coding task to a sandboxed Claude agent. Use for massive refactors or repo-wide audits.",
    "input_schema": {
        "type": "object",
        "properties": {
            "query": {"type": "string", "description": "The natural language instruction for Claude."}
        },
        "required": ["query"]
    }
}
