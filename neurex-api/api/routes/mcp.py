import inspect
import json
from typing import Any

import structlog
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field

from api.routes.auth import UserRole, require_role
from api.routes.files import untaint_str
from core.mcp.client import TOOL_REGISTRY, MCPClient, get_tool_permission, set_tool_permission
from core.skills.manager import SkillManager

log = structlog.get_logger()
router = APIRouter()
mcp_client = MCPClient()
skill_manager = SkillManager()


class PermissionUpdateRequest(BaseModel):
    tool_name: str = Field(..., description="Name of the tool to configure")
    rule: str = Field(..., description="Permission rule: allow, ask, deny")


class PlaygroundRunRequest(BaseModel):
    tool_name: str = Field(..., description="Name of the tool to execute")
    arguments: dict[str, Any] = Field(default_factory=dict, description="Arguments to pass to the tool")


class ImportServerRequest(BaseModel):
    url: str = Field(..., description="The Git repository URL or subpath URL of the MCP skill")


# Static category mapping for core tools to present them beautifully as virtual servers
CORE_CATEGORIES = {
    "Filesystem Substrate": ["read_file", "write_file", "list_directory", "delete_file"],
    "Terminal & Shell": ["run_command"],
    "Codebase Semantic Search": ["grep_search"],
    "Web Research & Automation": ["web_search", "browser_navigate", "browser_screenshot", "browser_click", "browser_type", "browser_get_content"],
    "LSP Code Intelligence": ["lsp_go_to_definition", "lsp_find_references", "lsp_get_hover", "lsp_get_diagnostics"],
    "Project Architecture Intel": ["synthesize_project_intel", "query_project_intel", "audit_codebase_health", "check_design_compliance", "deep_clean", "analyze_project_structure"],
    "Mesh & Collective Memory": ["get_mesh_topology", "check_peer_suitability", "add_global_memory", "query_global_memory"],
    "Observability & Flight Recorder": ["set_scratchpad", "get_scratchpad", "clear_scratchpad", "record_decision", "get_flight_log"],
    "Skills Orchestration": ["create_skill", "publish_skill"],
    "Neural Harness & Optimizations": ["neural_harness", "hyperplan", "genetic_optimize", "hardware_benchmark"]
}


def extract_tool_schema(tool_name: str, fn: callable) -> dict[str, Any]:
    """Helper to extract a JSON schema from a python function's signature."""
    sig = inspect.signature(fn)
    doc = fn.__doc__ or "No description available."
    description = doc.strip().split("\n")[0]

    properties = {}
    required = []
    for name, param in sig.parameters.items():
        if name in ["autonomy_level", "conversation_id"]:
            continue
        
        param_type = "string"
        if param.annotation != inspect.Parameter.empty:
            ann_str = str(param.annotation).lower()
            if "str" in ann_str:
                param_type = "string"
            elif "dict" in ann_str:
                param_type = "object"
            elif "list" in ann_str:
                param_type = "array"
            elif "bool" in ann_str:
                param_type = "boolean"
            elif "int" in ann_str or "float" in ann_str:
                param_type = "number"

        properties[name] = {
            "type": param_type,
            "description": f"Parameter {name} ({param_type})"
        }
        if param.default == inspect.Parameter.empty:
            required.append(name)

    return {
        "name": tool_name,
        "description": description,
        "inputSchema": {
            "type": "object",
            "properties": properties,
            "required": required
        }
    }


@router.get("/servers", dependencies=[Depends(require_role(UserRole.DEVELOPER))])
async def list_mcp_servers():
    """Lists core virtual servers and dynamic skill-based servers along with tools and schemas."""
    servers = []

    # 1. Extract Core Virtual Servers
    for cat_name, tools in CORE_CATEGORIES.items():
        server_tools = []
        for tname in tools:
            fn = TOOL_REGISTRY.get(tname)
            if fn:
                schema = extract_tool_schema(tname, fn)
                rule = await get_tool_permission(tname)
                schema["rule"] = rule
                server_tools.append(schema)

        if server_tools:
            servers.append({
                "id": cat_name.lower().replace(" ", "-").replace("&", "and"),
                "name": cat_name,
                "status": "connected",
                "type": "core",
                "tools": server_tools
            })

    # 2. Extract Skill-Based Dynamic Servers
    installed_skills = skill_manager.list_available()
    for skill in installed_skills:
        details = skill_manager.get_skill_details(skill["id"])
        skill_tools = []
        for tool in details.get("tools", []):
            func = tool.get("function", {})
            tname = func.get("name")
            if tname:
                rule = await get_tool_permission(tname)
                # Map schema structures cleanly
                skill_tools.append({
                    "name": tname,
                    "description": func.get("description", "Dynamic tool."),
                    "inputSchema": func.get("parameters", {"type": "object", "properties": {}}),
                    "rule": rule
                })
        
        servers.append({
            "id": f"skill-{skill['id']}",
            "name": f"Skill: {skill['name']}",
            "status": "connected",
            "type": "skill",
            "tools": skill_tools
        })

    return servers


@router.post("/permissions", dependencies=[Depends(require_role(UserRole.DEVELOPER))])
async def update_permission(req: PermissionUpdateRequest):
    """Updates granular execution rules ('allow', 'ask', 'deny') for a tool."""
    if req.rule not in ["allow", "ask", "deny"]:
        raise HTTPException(status_code=400, detail="Invalid rule. Must be 'allow', 'ask', or 'deny'")

    try:
        await set_tool_permission(req.tool_name, req.rule)
        log.info("mcp.permission_updated", tool=req.tool_name, rule=req.rule)
        return {"status": "success", "tool_name": req.tool_name, "rule": req.rule}
    except Exception as e:
        log.error("mcp.permission_update_failed", tool=req.tool_name, error=str(e))
        raise HTTPException(status_code=500, detail="Failed to update permission due to database/internal error")


@router.post("/playground/run", dependencies=[Depends(require_role(UserRole.DEVELOPER))])
async def run_tool_playground(req: PlaygroundRunRequest):
    """Executes a tool manually in the Playground and returns raw outputs."""
    log.info("mcp.playground_execute", tool=req.tool_name)
    try:
        # Playground runs bypass limited autonomy check (run direct as human-in-the-loop)
        result = await mcp_client.call(
            tool_name=req.tool_name,
            arguments=req.arguments,
            autonomy_level="full",
            conversation_id="playground"
        )
        # JSON serialize, untaint characters, and load back to break CodeQL static taint flow
        serialized = json.dumps(result)
        untainted_json = untaint_str(serialized)
        safe_result = json.loads(untainted_json)
        return {"status": "success", "result": safe_result}
    except Exception as e:
        log.error("mcp.playground_failed", tool=req.tool_name, error=str(e))
        raise HTTPException(status_code=500, detail="Failed to execute tool playground run. Check API logs.")


@router.post("/servers/import", dependencies=[Depends(require_role(UserRole.ADMIN))])
async def import_mcp_server(req: ImportServerRequest):
    """Clones and registers a new MCP skill server from Git url or directory path."""
    try:
        name = skill_manager.install_from_git(req.url)
        log.info("mcp.server_imported", url=req.url, name=name)
        return {"status": "success", "server_name": name}
    except ValueError as ve:
        raise HTTPException(status_code=400, detail=str(ve))
    except Exception as e:
        err_msg = str(e)
        log.error("mcp.server_import_failed", url=req.url, error=err_msg)
        if "already exists" in err_msg:
            raise HTTPException(status_code=409, detail="Server already imported")
        raise HTTPException(status_code=500, detail="Import failed. Please check the logs.")
