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
from core.mcp.tools.search import grep_search
from core.mcp.tools.researcher import web_search
from core.mcp.tools.browser import (
    browser_navigate, browser_screenshot, browser_click, browser_type, browser_get_content
)
from core.mcp.tools.workspace import deep_clean, analyze_project_structure
from core.mcp.tools.security import security_scan
from core.mcp.tools.intel import synthesize_project_intel, query_project_intel, audit_codebase_health, check_design_compliance
from core.mcp.tools.skills_builder import create_skill, publish_skill
from core.mcp.tools.mesh_intel import get_mesh_topology, check_peer_suitability
from core.context.scratchpad import set_scratchpad_value, get_scratchpad, clear_scratchpad
from core.observability.flight_recorder import record_decision, get_flight_log


log = structlog.get_logger()

TOOL_REGISTRY: dict[str, callable] = {
    "read_file":      read_file,
    "write_file":     write_file,
    "list_directory": list_directory,
    "delete_file":    delete_file,
    "run_command":    run_command,
    "grep_search":    grep_search,
    "web_search":     web_search,
    "browser_navigate":    browser_navigate,
    "browser_screenshot":  browser_screenshot,
    "browser_click":       browser_click,
    "browser_type":        browser_type,
    "browser_get_content": browser_get_content,
    "deep_clean":               deep_clean,
    "analyze_project_structure": analyze_project_structure,
    "security_scan":             security_scan,
    "synthesize_project_intel":  synthesize_project_intel,
    "query_project_intel":       query_project_intel,
    "audit_codebase_health":     audit_codebase_health,
    "check_design_compliance":   check_design_compliance,
    "create_skill":              create_skill,
    "publish_skill":             publish_skill,
    "get_mesh_topology":         get_mesh_topology,
    "check_peer_suitability":    check_peer_suitability,
    "set_scratchpad":            set_scratchpad_value,
    "get_scratchpad":            get_scratchpad,
    "clear_scratchpad":          clear_scratchpad,
    "record_decision":           record_decision,
    "get_flight_log":            get_flight_log,
}
class MCPClient:
    """
    Thin dispatcher. In a full MCP implementation this would speak the
    Model Context Protocol over stdio/HTTP. For now it directly calls
    Python implementations that are security-scoped.
    """
    def __init__(self):
        from core.skills.manager import SkillManager
        self.skills = SkillManager()

    async def call(self, tool_name: str, arguments: dict, autonomy_level: str = "limited", conversation_id: str | None = None) -> str:
        fn = TOOL_REGISTRY.get(tool_name)
        if fn is None:
            # Check SkillManager for dynamic tools
            skill_name = self.skills.get_skill_for_tool(tool_name)
            if skill_name:
                log.info("mcp.dispatch_to_skill", tool=tool_name, skill=skill_name)
                return await self.skills.execute_skill_tool(skill_name, tool_name, arguments)
                
            log.warning("mcp.unknown_tool", tool=tool_name)
            return f"Error: unknown tool '{tool_name}'"
        try:
            # Inject context-aware parameters
            import inspect
            sig = inspect.signature(fn)
            if "autonomy_level" in sig.parameters:
                arguments["autonomy_level"] = autonomy_level
            if "conversation_id" in sig.parameters and conversation_id:
                arguments["conversation_id"] = conversation_id
                
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
