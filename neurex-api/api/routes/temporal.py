"""
api/routes/temporal.py
Exposes Phase 53 Neural Temporal Synthesis telemetry for the frontend dashboard.
Handles neural snapshots, temporal restoration, and quantum simulation visualization.
"""

from fastapi import APIRouter

from core.infrastructure.quantum_sim import quantum_path_sim
from core.infrastructure.temporal import neural_temporal_registry

router = APIRouter(prefix="/api/temporal", tags=["Temporal"])

@router.get("/status")
async def get_temporal_status():
    """Returns the current state of neural snapshots and quantum sims."""
    snapshots = []
    for s_id, s in neural_temporal_registry.snapshots.items():
        snapshots.append({
            "id": s.id,
            "timestamp": s.timestamp.isoformat(),
            "reason": s.metadata.get("reason", "Unknown"),
            "status": s.status
        })

    return {
        "snapshots": snapshots,
        "temporal_coherence": 1.0,
        "quantum_active": True
    }

@router.post("/snapshots/capture")
async def capture_snapshot(reason: str):
    """Triggers a manual neural state snapshot."""
    s_id = await neural_temporal_registry.capture_state_snapshot(reason)
    return {"status": "success", "id": s_id}

@router.post("/snapshots/restore/{snapshot_id}")
async def restore_snapshot(snapshot_id: str):
    """Restores the neural soul to a previous snapshot."""
    success = await neural_temporal_registry.restore_temporal_state(snapshot_id)
    if success:
        return {"status": "success"}
    return {"status": "error", "message": "Snapshot not found."}

@router.get("/quantum/simulate")
async def run_simulation(target: str):
    """Triggers a quantum path simulation for a specific target."""
    path = await quantum_path_sim.simulate_refactor_paths(target, "dummy_logic")
    return {"status": "success", "best_path": path}
