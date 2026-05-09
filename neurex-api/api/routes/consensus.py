"""
api/routes/consensus.py
Exposes Phase 52 Universal Neural Consensus telemetry for the frontend dashboard.
Handles substrate bridges and neural law alignment status.
"""

from fastapi import APIRouter

from core.infrastructure.neural_law import neural_law
from core.infrastructure.substrate_sync import substrate_synchronizer

router = APIRouter(prefix="/api/consensus", tags=["Consensus"])

@router.get("/status")
async def get_consensus_status():
    """Returns the current state of universal consensus and substrate bridging."""
    external_nodes = []
    for node_id, node in substrate_synchronizer.external_nodes.items():
        external_nodes.append({
            "id": node.id,
            "name": node.name,
            "capacity": node.capacity_gb,
            "status": node.status,
            "bridged": node.id in substrate_synchronizer.active_bridges
        })

    return {
        "external_nodes": external_nodes,
        "protocols_enforced": neural_law.active_protocols,
        "alignment_level": 1.0, # 100% Protocol Alignment
        "consensus_active": True
    }

@router.post("/bridge/establish/{substrate_id}")
async def establish_bridge(substrate_id: str):
    """Manually establishes a bridge to an external compute substrate."""
    success = await substrate_synchronizer.establish_neural_bridge(substrate_id)
    if success:
        return {"status": "success", "message": f"Bridge to {substrate_id} established."}
    return {"status": "error", "message": "Failed to establish bridge."}

@router.get("/discovery")
async def trigger_discovery():
    """Manually triggers discovery of external compute substrates."""
    nodes = await substrate_synchronizer.discovery_external_substrates()
    return {"status": "success", "nodes_found": len(nodes)}
