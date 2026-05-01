"""
api/routes/evolution.py
Exposes Phase 48 Neural Evolution telemetry for the frontend dashboard.
"""
from fastapi import APIRouter, Depends
from typing import List, Dict, Any
from core.infrastructure.evolution import evolution_coordinator
from core.infrastructure.arch_mutator import arch_mutator

router = APIRouter(prefix="/api/evolution", tags=["Evolution"])

@router.get("/status")
async def get_evolution_status():
    """Returns the current state of all neural adapters and their architectural specs."""
    status = []
    for domain, adapter in evolution_coordinator.adapters.items():
        spec = arch_mutator.specs.get(domain)
        status.append({
            "domain": domain,
            "adapter_id": adapter.id,
            "version": adapter.version,
            "fitness": round(adapter.fitness_score, 2),
            "rank": spec.rank if spec else 8,
            "alpha": spec.alpha if spec else 16,
            "modules": spec.target_modules if spec else ["q_proj", "v_proj"]
        })
    return {"adapters": status}

@router.post("/reset/{domain}")
async def reset_adapter(domain: str):
    """Manually resets an adapter to its base state."""
    if domain in evolution_coordinator.adapters:
        evolution_coordinator.adapters[domain].fitness_score = 0.0
        evolution_coordinator.adapters[domain].version = 1
        return {"status": "success", "message": f"Adapter {domain} reset."}
    return {"status": "error", "message": "Domain not found."}
