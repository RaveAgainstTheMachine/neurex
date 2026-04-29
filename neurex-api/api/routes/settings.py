"""
api/routes/settings.py
Endpoints for managing dynamic platform settings.
Port changes automatically re-apply cross-platform firewall rules.
"""
from fastapi import APIRouter, HTTPException, Depends, BackgroundTasks
from pydantic import BaseModel
from typing import Dict, Any
import os
from core.settings.manager import settings_manager
from api.routes.auth import require_role, UserRole
from core.task_graph import User

router = APIRouter()

# Keys that, when changed, require firewall re-application
PORT_KEYS = {"api_port", "web_port", "chromadb_port", "ollama_port", "rpc_port",
             "firewall_enabled", "firewall_lan_only"}


class SettingsUpdateRequest(BaseModel):
    settings: Dict[str, Any]


async def _reapply_firewall() -> dict:
    """Re-apply firewall rules using current settings. Called in background."""
    if not settings_manager.get("firewall_enabled"):
        return {"skipped": "firewall_disabled"}

    from core.infrastructure.firewall import firewall_manager
    role = os.getenv("NODE_ROLE", "master")
    bind_ip = os.getenv("BIND_IP", "0.0.0.0")

    return await firewall_manager.apply_rules(
        role=role,
        bind_ip=bind_ip,
        api_port=settings_manager.get("api_port"),
        web_port=settings_manager.get("web_port"),
        chromadb_port=settings_manager.get("chromadb_port"),
        ollama_port=settings_manager.get("ollama_port"),
        rpc_port=settings_manager.get("rpc_port"),
        lan_only=settings_manager.get("firewall_lan_only"),
    )


@router.get("/")
async def get_settings():
    return settings_manager.get_all()


# Settings that ONLY Admins can change
ADMIN_ONLY_SETTINGS = {
    "api_port", "web_port", "chromadb_port", "ollama_port", "rpc_port",
    "firewall_enabled", "firewall_lan_only", "enable_mesh_routing",
    "enable_distributed_pooling", "ollama_base_url"
}


@router.post("/")
async def update_settings(
    req: SettingsUpdateRequest, 
    background_tasks: BackgroundTasks,
    current_user: User = Depends(require_role(UserRole.DEVELOPER))
):
    # If not admin, ensure they aren't changing restricted keys
    if current_user.role != UserRole.ADMIN:
        restricted_changes = [k for k in req.settings if k in ADMIN_ONLY_SETTINGS]
        if restricted_changes:
            raise HTTPException(
                status_code=403, 
                detail=f"Admin privileges required to modify: {', '.join(restricted_changes)}"
            )

    # Detect if any port or firewall key is being changed
    firewall_needs_update = any(k in PORT_KEYS for k in req.settings)

    for key, value in req.settings.items():
        settings_manager.update(key, value)

    # Sync infrastructure services
    from core.infrastructure.insomnia import insomnia_service
    insomnia_service.sync()

    from core.infrastructure.distributed import distributed_manager
    if settings_manager.get("enable_distributed_pooling"):
        await distributed_manager.start_rpc_server()
    else:
        distributed_manager.stop_rpc_server()

    # Re-apply firewall rules in background if ports changed
    if firewall_needs_update and settings_manager.get("firewall_enabled"):
        background_tasks.add_task(_reapply_firewall)

    return {
        "status": "success",
        "settings": settings_manager.get_all(),
        "firewall_update_triggered": firewall_needs_update,
    }


@router.get("/firewall/status")
async def get_firewall_status(_=Depends(require_role(UserRole.ADMIN))):
    """
    Returns current firewall configuration and platform details.
    Useful for the Settings UI to show which ports are protected.
    """
    from core.infrastructure.firewall import firewall_manager
    role = os.getenv("NODE_ROLE", "master")

    return {
        "enabled": settings_manager.get("firewall_enabled"),
        "platform": firewall_manager.platform_name,
        "role": role,
        "lan_only": settings_manager.get("firewall_lan_only"),
        "protected_ports": {
            "api_port":      settings_manager.get("api_port"),
            "web_port":      settings_manager.get("web_port"),
            "chromadb_port": settings_manager.get("chromadb_port"),
            "ollama_port":   settings_manager.get("ollama_port"),
            "rpc_port":      settings_manager.get("rpc_port"),
        } if role == "master" else {
            "rpc_port": settings_manager.get("rpc_port"),
        }
    }


@router.post("/firewall/apply", dependencies=[Depends(require_role(UserRole.ADMIN))])
async def force_firewall_apply(background_tasks: BackgroundTasks):
    """
    Manually trigger a full firewall rule re-application.
    Useful after system reboots or manual rule tampering.
    """
    if not settings_manager.get("firewall_enabled"):
        return {"status": "skipped", "reason": "firewall_disabled"}
    background_tasks.add_task(_reapply_firewall)
    return {"status": "applying"}
