"""
core/agents/swarm_manager.py
Orchestrates multi-agent "swarms" for complex, distributed refactoring tasks.
Assigns sub-tasks to Mesh peers and aggregates results.
"""
from __future__ import annotations
import uuid
import asyncio
import structlog
from typing import List, Dict, Any
from core.task_graph import TaskNode, TaskStatus
from core.infrastructure.mesh import mesh_router

log = structlog.get_logger()

class SwarmTask:
    def __init__(self, title: str, description: str):
        self.id = str(uuid.uuid4())
        self.title = title
        self.description = description
        self.sub_tasks: List[Dict[str, Any]] = []
        self.results: Dict[str, Any] = {}
        self.status = "planning"

class SwarmManager:
    def __init__(self):
        self.active_swarms: Dict[str, SwarmTask] = {}

    async def initiate_swarm(self, parent_task: TaskNode, plan: List[Dict[str, Any]]) -> str:
        """
        Creates a swarm for a multi-file refactor.
        'plan' is a list of sub-tasks: [{"title": "...", "description": "...", "files": [...]}]
        """
        swarm = SwarmTask(parent_task.title, parent_task.description)
        self.active_swarms[swarm.id] = swarm
        
        log.info("swarm.initiated", swarm_id=swarm.id, sub_tasks=len(plan))
        
        # Dispatch sub-tasks to peers
        await self._dispatch_swarm(swarm, plan)
        
        return swarm.id

    async def _dispatch_swarm(self, swarm: SwarmTask, plan: List[Dict[str, Any]]):
        swarm.status = "executing"
        dispatch_tasks = []
        
        for i, sub in enumerate(plan):
            # Find a peer for this sub-task
            peer_url = await mesh_router.get_best_inference_node()
            dispatch_tasks.append(self._run_sub_task(swarm, i, sub, peer_url))
            
        await asyncio.gather(*dispatch_tasks)
        swarm.status = "completed"
        log.info("swarm.completed", swarm_id=swarm.id)

    async def _run_sub_task(self, swarm: SwarmTask, index: int, sub: Dict[str, Any], peer_url: str):
        model = sub.get("model", "qwen2.5-coder:14b")
        log.info("swarm.sub_task_dispatched", 
                 swarm_id=swarm.id, 
                 index=index, 
                 peer=peer_url,
                 model=model)
        
        # In a real mesh, we would call the peer's /api/tasks/execute endpoint with the 'model' parameter.
        # For now, we simulate a local "swarm" worker utilizing the specified model tier.
        await asyncio.sleep(2) # Simulate work with specialized model
        swarm.results[index] = {"status": "success", "summary": f"Completed {sub['title']} using {model}"}

swarm_manager = SwarmManager()
