"""
api/routes/infra.py
Endpoints for managing AI infrastructure (engines, VRAM, performance).
"""

from pathlib import Path
from typing import Any

from fastapi import APIRouter, Depends, HTTPException

from api.routes.auth import UserRole, require_role
from api.routes.files import untaint_path
from core.infrastructure.benchmarker import hardware_benchmarker as benchmarker
from core.infrastructure.manager import InfrastructureManager
from core.infrastructure.registry import LLMRecommender, search_huggingface
from core.skills.manager import SkillManager

router = APIRouter()
infra_manager = InfrastructureManager()
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


@router.delete("/skills/{skill_id}", dependencies=[Depends(require_role(UserRole.ADMIN))])
async def delete_skill(skill_id: str):
    """Purge a community skill from the node."""
    from core.logger import log

    log.info("infra.skill_delete_request", skill_id=skill_id)
    if skill_manager.delete_skill(skill_id):
        log.info("infra.skill_deleted", skill_id=skill_id)
        return {"status": "deleted"}
    log.warning(
        "infra.skill_delete_failed",
        skill_id=skill_id,
        reason="not_found",
        path=str(skill_manager.SKILLS_DIR / skill_id),
    )
    raise HTTPException(
        status_code=404,
        detail=f"Skill '{skill_id}' not found at {skill_manager.SKILLS_DIR / skill_id}",
    )


@router.post("/benchmark/{model}", dependencies=[Depends(require_role(UserRole.DEVELOPER))])
async def run_benchmark(model: str):
    """Run a performance benchmark against a specific model."""
    return await benchmarker.run_benchmark(model)


@router.get("/status")
async def get_infra_status():
    """Get status of all supported inference engines and system metrics."""
    engines = await infra_manager.get_status()
    metrics = infra_manager.get_system_metrics()
    local_models = await infra_manager.get_installed_models("ollama")

    # Include latest benchmark if available
    metrics["benchmarks"] = benchmarker.last_results

    # Include project intelligence if available
    import json
    import os

    ws = os.getenv("WORKSPACE_PATH", "/workspace")
    intel_path = os.path.join(ws, ".neurex", "intel.json")
    if os.path.exists(intel_path):
        try:
            with open(intel_path) as f:
                metrics["intel"] = json.load(f)
        except Exception:
            pass

    # Include distributed info
    from core.infrastructure.distributed import distributed_manager

    distributed = distributed_manager.get_status()

    return {
        "engines": engines,
        "metrics": metrics,
        "local_models": local_models,
        "distributed": distributed,
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


@router.post("/engine/{name}/install", dependencies=[Depends(require_role(UserRole.ADMIN))])
async def install_engine(name: str):
    """Install a specific AI engine."""
    try:
        success = await infra_manager.install_engine(name)
        return {"success": success}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


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
    """List only the models actually available on this node."""
    local_models = await infra_manager.get_installed_models("ollama")

    # Group local models by base name (e.g. qwen2.5-coder)
    grouped: dict[str, dict[str, Any]] = {}

    for lm in local_models:
        if not isinstance(lm, dict):
            continue

        base_name = lm["name"].split(":")[0]
        if base_name not in grouped:
            grouped[base_name] = {
                "name": base_name,
                "engine": "ollama",
                "params": lm.get("params", "Local"),
                "size_gb": lm.get("size_gb", 0),
                "context_window": 32768,
                "vram_required_gb": 0,
                "recommended_tasks": [],
                "is_downloaded": True,
                "is_community": False,
                "is_active": lm.get("is_active", False),
                "origin": "LOCAL",
                "variants": [],
            }

        # Add this specific tag as a variant
        grouped[base_name]["variants"].append(
            {
                "name": lm["name"],
                "size_gb": lm.get("size_gb", 0),
                "params": lm.get("params", "Local"),
            }
        )

        # Update aggregate active state
        if lm.get("is_active"):
            grouped[base_name]["is_active"] = True

    return list(grouped.values())


@router.post("/model/pull", dependencies=[Depends(require_role(UserRole.ADMIN))])
async def pull_model(engine: str, model: str):
    """Initiate a model download."""
    try:
        success = await infra_manager.pull_model(engine, model)
        return {"success": success}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ── Mesh Federation ──
import httpx
from fastapi import Request
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

from core.infrastructure.mesh import mesh_router


class PeerRequest(BaseModel):
    url: str
    token: str
    name: str


from fastapi import Response


@router.get("/mesh/sync/manifest")
async def get_sync_manifest():
    """Retrieve the manifest of files in the workspace (hashes, sizes, mtimes)."""
    from core.infrastructure.mesh import generate_local_manifest
    return {"manifest": generate_local_manifest()}


@router.get("/mesh/sync/download")
async def download_sync_file(path: str):
    """Download a file from the workspace for peer syncing."""
    import os

    from core.infrastructure.mesh import get_workspace_root
    
    workspace = get_workspace_root()
    try:
        safe_root = os.path.realpath(str(workspace))
        target = os.path.realpath(os.path.join(safe_root, path))
        safe_prefix = safe_root if safe_root.endswith(os.sep) else safe_root + os.sep
        
        if target == safe_root:
            pass
        elif target.startswith(safe_prefix):
            pass
        else:
            raise PermissionError("Path traversal blocked")
            
        resolved = untaint_path(Path(target))
        if not resolved or not resolved.is_file():  # lgtm [py/path-injection]
            raise HTTPException(status_code=404, detail="File not found")
        content = resolved.read_bytes()  # lgtm [py/path-injection]
        return Response(content=content, media_type="application/octet-stream")
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/mesh/sync/upload")
async def upload_sync_file(path: str, mtime: float, request: Request):
    """Upload a file to the workspace from a peer during sync."""
    import os

    from core.infrastructure.mesh import get_workspace_root
    
    workspace = get_workspace_root()
    try:
        safe_root = os.path.realpath(str(workspace))
        target = os.path.realpath(os.path.join(safe_root, path))
        safe_prefix = safe_root if safe_root.endswith(os.sep) else safe_root + os.sep
        
        if target == safe_root:
            pass
        elif target.startswith(safe_prefix):
            pass
        else:
            raise PermissionError("Path traversal blocked")
            
        resolved = untaint_path(Path(target))
        if not resolved:
            raise HTTPException(status_code=400, detail="Invalid path")
        resolved.parent.mkdir(parents=True, exist_ok=True)  # lgtm [py/path-injection]
        content = await request.body()
        resolved.write_bytes(content)  # lgtm [py/path-injection]
        os.utime(resolved, (mtime, mtime))  # lgtm [py/path-injection]
        return {"status": "success"}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))



@router.get("/engines")
async def get_engines():
    """Returns status of all inference engines."""
    return await infra_manager.get_status()


@router.get("/metrics")
async def get_metrics():
    """Returns current system metrics."""
    metrics = infra_manager.get_system_metrics()
    metrics["benchmarks"] = benchmarker.last_results
    return metrics


@router.get("/peers")
async def get_peers_simple():
    """Direct peer list for the frontend store."""
    return [p.to_dict() for p in mesh_router.peers.values()]


@router.get("/mesh/peers", dependencies=[Depends(require_role(UserRole.DEVELOPER))])
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
            headers={k: v for k, v in request.headers.items() if k.lower() != "host"},
            content=request.stream(),
        ) as resp:
            async for chunk in resp.aiter_bytes():
                yield chunk

    return StreamingResponse(stream_generator(), media_type="application/json")


@router.get("/logs", dependencies=[Depends(require_role(UserRole.ADMIN))])
async def get_system_logs():
    """Retrieve the latest system audit logs."""
    from core.logger import get_audit_logs

    return get_audit_logs(limit=100)


@router.get("/registry/search")
async def search_registry(query: str):
    """Search Hugging Face for GGUF models."""
    return await search_huggingface(query)


# ── Neurex Somnus (autoDream) ──
import os

from core.harness.somnus import somnus_daemon


@router.post("/somnus/start", dependencies=[Depends(require_role(UserRole.ADMIN))])
async def start_somnus():
    """Start the Somnus background architectural monitor."""
    ws = os.getenv("WORKSPACE_PATH", os.getcwd())
    somnus_daemon.start(ws)
    return {"status": "started", "workspace": ws}


@router.post("/somnus/stop", dependencies=[Depends(require_role(UserRole.ADMIN))])
async def stop_somnus():
    """Stop the Somnus background architectural monitor."""
    somnus_daemon.stop()
    return {"status": "stopped"}


@router.get("/somnus/status")
async def get_somnus_status():
    """Check if the Somnus daemon is active."""
    return {"is_running": somnus_daemon.is_running}
