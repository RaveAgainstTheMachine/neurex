"""
api/routes/infra.py
Endpoints for managing AI infrastructure (engines, VRAM, performance).
"""
from fastapi import APIRouter, HTTPException, Depends
from typing import List, Dict, Any
from core.infrastructure.manager import InfrastructureManager
from core.infrastructure.registry import LLMRecommender, MODEL_REGISTRY
from core.infrastructure.benchmarker import Benchmarker
from core.skills.manager import SkillManager

router = APIRouter()
infra_manager = InfrastructureManager()
benchmarker = Benchmarker()
skill_manager = SkillManager()

@router.get("/skills")
async def list_skills():
    """List all available and pre-baked skills."""
    return skill_manager.list_available()

@router.post("/skills/{skill_id}/toggle")
async def toggle_skill(skill_id: str, enable: bool):
    """Enable or disable a specific skill."""
    success = skill_manager.toggle_skill(skill_id, enable)
    if not success:
        raise HTTPException(status_code=404, detail="Skill not found")
    return {"status": "success", "enabled": enable}

@router.post("/benchmark/{model}")
async def run_benchmark(model: str):
    """Run a performance benchmark against a specific model."""
    return await benchmarker.run_benchmark(model)

@router.get("/status")
async def get_infra_status():
    """Get status of all supported inference engines."""
    return await infra_manager.get_status()

@router.post("/engine/{name}/start")
async def start_engine(name: str):
    """Start a specific AI engine."""
    try:
        success = await infra_manager.start_engine(name)
        return {"success": success}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/engine/{name}/stop")
async def stop_engine(name: str):
    """Stop a specific AI engine."""
    success = await infra_manager.stop_engine(name)
    return {"success": success}

@router.get("/recommend")
async def recommend_model(task: str):
    """Recommend the best available model for a task."""
    vram = infra_manager.get_system_vram()
    recommendation = LLMRecommender.recommend(task, vram)
    if not recommendation:
        raise HTTPException(status_code=404, detail="No suitable model found")
    return recommendation

@router.get("/registry")
async def get_model_registry():
    """List all models known to Neurex and their capabilities."""
    return MODEL_REGISTRY
