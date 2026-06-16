"""
core/mcp/tools/install_tool.py
Tool to download a model and update active settings routing.
"""

from __future__ import annotations

import structlog

from core.infrastructure.manager import InfrastructureManager
from core.settings.manager import settings_manager

log = structlog.get_logger()
infra_manager = InfrastructureManager()

async def install_and_route_model(model_name: str, task_role: str, engine: str = "ollama") -> str:
    """
    Download/pull a model and route the specified task role to it.
    """
    log.info("tools.install_and_route_model.start", model=model_name, role=task_role, engine=engine)
    try:
        # 1. Pull the model
        success = await infra_manager.pull_model(engine, model_name)
        if not success:
            return f"Failed to install model {model_name} via engine {engine}."

        # 2. Update model routes in settings
        routes = settings_manager.get("model_routes") or {}
        routes[task_role] = model_name
        settings_manager.update("model_routes", routes, scope="global")

        log.info("tools.install_and_route_model.success", model=model_name, role=task_role)
        return f"Successfully installed and routed '{model_name}' for task role '{task_role}'."
    except Exception as e:
        log.error("tools.install_and_route_model.failed", error=str(e))
        return f"Error executing install_and_route_model: {str(e)}"
