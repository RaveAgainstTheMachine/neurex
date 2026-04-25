"""
api/routes/settings.py
Endpoints for managing dynamic platform settings.
"""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Dict, Any
from core.settings.manager import settings_manager

router = APIRouter()

class SettingsUpdateRequest(BaseModel):
    settings: Dict[str, Any]

@router.get("/")
async def get_settings():
    return settings_manager.get_all()

@router.post("/")
async def update_settings(req: SettingsUpdateRequest):
    for key, value in req.settings.items():
        settings_manager.update(key, value)
    return {"status": "success", "settings": settings_manager.get_all()}
