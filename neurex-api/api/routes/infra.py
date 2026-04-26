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

from core.skills.manager import SkillManager
from api.routes.auth import require_role, UserRole

router = APIRouter()
infra_manager = InfrastructureManager()
benchmarker = Benchmarker()
skill_manager = SkillManager()

@router.get("/skills")
async def list_skills():
    """List all available and pre-baked skills."""
    return skill_manager.list_available()

@router.post("/skills/{skill_id}/toggle", dependencies=[Depends(require_role(UserRole.ADMIN))])
async def toggle_skill(skill_id: str, enable: bool):
    """Enable or disable a specific skill."""
    success = skill_manager.toggle_skill(skill_id, enable)
    if not success:
        raise HTTPException(status_code=404, detail="Skill not found")
    return {"status": "success", "enabled": enable}

@router.post("/benchmark/{model}", dependencies=[Depends(require_role(UserRole.DEVELOPER))])
async def run_benchmark(model: str):
    """Run a performance benchmark against a specific model."""
    return await benchmarker.run_benchmark(model)

@router.get("/status")
async def get_infra_status():
    """Get status of all supported inference engines and system metrics."""
    engines = await infra_manager.get_status()
    metrics = infra_manager.get_system_metrics()
    return {
        "engines": engines,
        "metrics": metrics
    }

@router.post("/engine/{name}/start", dependencies=[Depends(require_role(UserRole.ADMIN))])
async def start_engine(name: str):
    """Start a specific AI engine."""
    try:
        success = await infra_manager.start_engine(name)
        return {"success": success}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/engine/{name}/stop", dependencies=[Depends(require_role(UserRole.ADMIN))])
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

@router.post("/model/pull", dependencies=[Depends(require_role(UserRole.ADMIN))])
async def pull_model(engine: str, model: str):
    """Initiate a model download."""
    try:
        success = await infra_manager.pull_model(engine, model)
        return {"success": success}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# ── Mesh Federation ──
from core.infrastructure.mesh import mesh_router
from pydantic import BaseModel
import httpx
from fastapi.responses import StreamingResponse
from fastapi import Request

class PeerRequest(BaseModel):
    url: str
    token: str
    name: str

@router.get("/mesh/peers")
async def list_peers():
    return [p.to_dict() for p in mesh_router.peers.values()]

@router.post("/mesh/peers", dependencies=[Depends(require_role(UserRole.ADMIN))])
async def add_peer(req: PeerRequest):
    success = mesh_router.add_peer(req.url, req.token, req.name)
    if not success:
        raise HTTPException(status_code=400, detail="Peer already exists")
    return {"status": "success"}

@router.delete("/mesh/peers", dependencies=[Depends(require_role(UserRole.ADMIN))])
async def remove_peer(url: str):
    mesh_router.remove_peer(url)
    return {"status": "deleted"}

@router.post("/ollama_proxy/{path:path}", dependencies=[Depends(require_role(UserRole.DEVELOPER))])
async def ollama_proxy(path: str, request: Request):
    """
    Reverse proxy for Ollama inference. Allows authorized peer nodes 
    to use this node's GPU for generation.
    """
    import os
    ollama_base = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
    target_url = f"{ollama_base}/{path}"
    
    client = httpx.AsyncClient()
    
    async def stream_generator():
        async with client.stream(
            method=request.method,
            url=target_url,
            headers={k: v for k, v in request.headers.items() if k.lower() != 'host'},
            content=request.stream()
        ) as resp:
            async for chunk in resp.aiter_bytes():
                yield chunk

    return StreamingResponse(stream_generator(), media_type="application/json")
