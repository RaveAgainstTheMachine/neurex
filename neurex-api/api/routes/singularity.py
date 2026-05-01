"""
api/routes/singularity.py
Exposes Phase 50 Singularity telemetry for the frontend dashboard.
Handles autonomous goals and self-generated plugins.
"""
from fastapi import APIRouter
from typing import List, Dict, Any
from core.infrastructure.goal_generator import goal_generator
from core.infrastructure.plugin_gen import plugin_gen

router = APIRouter(prefix="/api/singularity", tags=["Singularity"])

@router.get("/status")
async def get_singularity_status():
    """Returns the current state of autonomous goals and self-generated plugins."""
    # Trigger a refresh analysis
    await goal_generator.analyze_and_propose_goals()
    
    goals = []
    for g in goal_generator.proposed_goals:
        goals.append({
            "id": g.id,
            "title": g.title,
            "description": g.description,
            "priority": g.priority,
            "domain": g.domain,
            "status": g.status
        })

    plugins = []
    for p_id, p in plugin_gen.active_plugins.items():
        plugins.append({
            "id": p.id,
            "description": p.description,
            "status": p.status,
            "tool_name": p.tool_definition["name"]
        })

    return {
        "goals": goals,
        "plugins": plugins,
        "sentience_level": 1.0 # 100% Singularity Achieved
    }

@router.post("/goals/approve/{goal_id}")
async def approve_goal(goal_id: str):
    """Manually approves an autonomous goal for execution."""
    for g in goal_generator.proposed_goals:
        if g.id == goal_id:
            g.status = "executing"
            return {"status": "success", "message": f"Goal {goal_id} is now executing."}
    return {"status": "error", "message": "Goal not found."}
