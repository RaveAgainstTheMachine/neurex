"""
api/routes/synthesis.py
Exposes Phase 51 Neural Self-Synthesis telemetry for the frontend dashboard.
Handles project inceptions, self-optimizations, and governance DAO.
"""

from fastapi import APIRouter

from core.infrastructure.governance import governance_dao
from core.infrastructure.inceptor import project_inceptor
from core.infrastructure.self_optimizer import self_optimizer

router = APIRouter(prefix="/api/synthesis", tags=["Self-Synthesis"])

@router.get("/status")
async def get_synthesis_status():
    """Returns the current state of self-synthesis activities."""
    inceptions = []
    for name, path in project_inceptor.active_inceptions.items():
        inceptions.append({"name": name, "path": path})

    optimizations = []
    for opt in self_optimizer.pending_optimizations.values():
        optimizations.append({
            "id": opt["id"],
            "target": opt["target_file"],
            "reason": opt["reason"],
            "status": opt["status"]
        })

    proposals = []
    for p_id, p in governance_dao.proposals.items():
        proposals.append({
            "id": p.id,
            "title": p.title,
            "description": p.description,
            "status": p.status,
            "votes": {
                "total": len(p.votes),
                "support": sum(1 for v in p.votes.values() if v)
            }
        })

    return {
        "inceptions": inceptions,
        "optimizations": optimizations,
        "proposals": proposals,
        "synthesis_integrity": 1.0
    }

@router.post("/proposals/vote/{proposal_id}")
async def vote_proposal(proposal_id: str, support: bool):
    """Allows a user/node to vote on a governance proposal."""
    await governance_dao.cast_vote(proposal_id, "user-node", support)
    return {"status": "success"}

@router.post("/optimizations/apply/{opt_id}")
async def apply_optimization(opt_id: str):
    """Manually applies a core self-optimization."""
    await self_optimizer.apply_self_optimization(opt_id)
    return {"status": "success"}
