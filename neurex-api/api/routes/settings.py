"""
api/routes/settings.py
Endpoints for managing dynamic platform settings.
"""
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import Dict, Any
from core.settings.manager import settings_manager
from api.routes.auth import require_role, UserRole

router = APIRouter()

class SettingsUpdateRequest(BaseModel):
    settings: Dict[str, Any]

@router.get("/")
async def get_settings():
    return settings_manager.get_all()

@router.post("/", dependencies=[Depends(require_role(UserRole.ADMIN))])
async def update_settings(req: SettingsUpdateRequest):
    for key, value in req.settings.items():
        settings_manager.update(key, value)
    
    # Sync system services
    from core.infrastructure.insomnia import insomnia_service
    insomnia_service.sync()
    
    return {"status": "success", "settings": settings_manager.get_all()}
