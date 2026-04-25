"""
core/mcp/client.py
MCP tool dispatcher. Routes tool names to concrete tool implementations.
Add new tools here and register them in TOOL_REGISTRY.
"""
from __future__ import annotations
import structlog
from core.mcp.tools.filesystem import (
    read_file, write_file, list_directory, delete_file
)
from core.mcp.tools.terminal import run_command
from core.mcp.tools.researcher import web_search
from core.mcp.tools.browser import (
    browser_navigate, browser_screenshot, browser_click, browser_type, browser_get_content
)


log = structlog.get_logger()

TOOL_REGISTRY: dict[str, callable] = {
    "read_file":      read_file,
    "write_file":     write_file,
    "list_directory": list_directory,
    "delete_file":    delete_file,
    "run_command":    run_command,
    "web_search":     web_search,
    "browser_navigate":    browser_navigate,
    "browser_screenshot":  browser_screenshot,
    "browser_click":       browser_click,
    "browser_type":        browser_type,
    "browser_get_content": browser_get_content,
}



class MCPClient:
    """
    Thin dispatcher. In a full MCP implementation this would speak the
    Model Context Protocol over stdio/HTTP. For now it directly calls
    Python implementations that are security-scoped.
    """

    async def call(self, tool_name: str, arguments: dict, autonomy_level: str = "limited") -> str:
        fn = TOOL_REGISTRY.get(tool_name)
        if fn is None:
            log.warning("mcp.unknown_tool", tool=tool_name)
            return f"Error: unknown tool '{tool_name}'"
        try:
            # Inject autonomy_level into arguments if the tool supports it
            import inspect
            sig = inspect.signature(fn)
            if "autonomy_level" in sig.parameters:
                arguments["autonomy_level"] = autonomy_level
                
            result = await fn(**arguments)
            return str(result)
        except PermissionError as e:
            log.error("mcp.permission_denied", tool=tool_name, error=str(e))
            return f"Permission denied: {e}"
        except Exception as e:
            log.error("mcp.tool_error", tool=tool_name, error=str(e))
            return f"Tool error: {e}"

    def list_tools(self) -> list[str]:
        return list(TOOL_REGISTRY.keys())
