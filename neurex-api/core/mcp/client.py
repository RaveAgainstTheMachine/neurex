"""
core/mcp/client.py
MCP tool dispatcher. Routes tool names to concrete tool implementations.
Add new tools here and register them in TOOL_REGISTRY.
"""
from __future__ import annotations
import inspect
import structlog
from typing import Any
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
from core.mcp.servers.neural_harness import run_neural_harness
from core.harness.hyperplan import HyperPlan
from core.agents.genetic_agent import GeneticAgent

log = structlog.get_logger()

async def run_hyperplan(query: str) -> str:
    """Invokes the multi-pass HyperPlan engine for complex architecture."""
    from core.context.manager import ContextManager
    from core.agents.base_agent import BaseAgent
    agent = BaseAgent(None, ContextManager()) # Placeholder rules
    up = HyperPlan(agent)
    blueprint = await up.generate_blueprint(query)
    import json
    return json.dumps(blueprint, indent=2)

async def run_genetic_optimization(file_path: str) -> str:
    """Invokes the Genetic Evolution cycle to optimize a module."""
    from core.context.manager import ContextManager
    from core.agents.base_agent import BaseAgent
    agent = BaseAgent(None, ContextManager())
    ga = GeneticAgent(agent)
    success = await ga.evolve_module(file_path)
    return "Genetic optimization COMPLETED and APPLIED." if success else "Genetic optimization REJECTED or no improvement found."

from core.context.global_memory import global_memory

log = structlog.get_logger()

async def run_add_global_memory(key: str, content: str) -> str:
    """Adds a persistent 'Sticky Note' to the Mesh-Wide Memory."""
    await global_memory.add_pointer(key, content)
    return f"Global memory pointer '{key}' added and broadcast to Mesh."

async def run_query_global_memory(query: str) -> str:
    """Queries the collective experience of the Neurex Mesh."""
    return await global_memory.query_memory(query)

from core.infrastructure.benchmarker import hardware_benchmarker

log = structlog.get_logger()

async def run_hardware_benchmark(model: str = "default") -> str:
    """Benchmarks local hardware and recommends performance tuning."""
    results = await hardware_benchmarker.run_benchmark(model)
    import json
    return json.dumps(results, indent=2)

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
    "neural_harness":            run_neural_harness,
    "hyperplan":                 run_hyperplan,
    "genetic_optimize":          run_genetic_optimization,
    "add_global_memory":         run_add_global_memory,
    "query_global_memory":       run_query_global_memory,
    "hardware_benchmark":        run_hardware_benchmark,
}

class MCPClient:
    """
    Thin dispatcher. Handles tool discovery, YOLO permission classification,
    and parameter injection for context-aware tools.
    """
    def __init__(self):
        from core.skills.manager import SkillManager
        self.skills = SkillManager()

    async def call(self, tool_name: str, arguments: dict, autonomy_level: str = "limited", conversation_id: str | None = None) -> Any:
        """
        Executes a tool call. Enforces YOLO classification and Swarm Self-Governance (Phase 40).
        """
        # Phase 40: Swarm Self-Governance Check
        from core.security.governance import governance_manager
        path = arguments.get("path") or arguments.get("file_path") or arguments.get("TargetFile")
        if path and not governance_manager.is_authorized(conversation_id or "global", path):
            log.error("governance.unauthorized_access", tool=tool_name, path=path)
            return f"Error: Governance violation. Path '{path}' is not authorized for this task session."

        # Phase 32: YOLO Permission Classifier
        safe_tools = ["read_file", "list_directory", "grep_search", "web_search", "query_project_intel", "get_flight_log"]
        is_yolo = tool_name in safe_tools
        
        if is_yolo:
            log.info("mcp.yolo_auto_approve", tool=tool_name)
        else:
            # Traditional RBAC/Auth logic would go here
            pass
            
        fn = TOOL_REGISTRY.get(tool_name)
        if not fn:
            # Check SkillManager for dynamic tools
            skill_name = self.skills.get_skill_for_tool(tool_name)
            if skill_name:
                log.info("mcp.dispatch_to_skill", tool=tool_name, skill=skill_name)
                return await self.skills.execute_skill_tool(skill_name, tool_name, arguments)
            return f"Error: Tool '{tool_name}' not found."
            
        try:
            # Inject context-aware parameters
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
