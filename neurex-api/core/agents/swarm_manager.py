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
        Phase 44: Hive-Mind Sharding integration.
        """
        from core.collaboration.hive_manager import hive_manager
        
        swarm = SwarmTask(parent_task.title, parent_task.description)
        self.active_swarms[swarm.id] = swarm
        
        log.info("swarm.initiated", swarm_id=swarm.id, sub_tasks=len(plan))
        
        # Phase 44: Hive-Mind Sharding
        blueprint = {"steps": plan}
        shards = await hive_manager.shard_blueprint(swarm.id, blueprint)
        
        # Dispatch shards to peers
        dispatch_plan = []
        for shard in shards:
            if await hive_manager.claim_shard(swarm.id, shard["shard_id"]):
                dispatch_plan.append(shard["step"])
        
        if dispatch_plan:
            await self._dispatch_swarm(swarm, dispatch_plan)
            
            # Release shards after dispatch (simplified for Phase 44 logic)
            for shard in shards:
                hive_manager.release_shard(swarm.id, shard["shard_id"])
        
        return swarm.id

    async def _dispatch_swarm(self, swarm: SwarmTask, plan: List[Dict[str, Any]]):
        swarm.status = "executing"
        dispatch_tasks = []
        
        from core.infrastructure.compute_monitor import compute_monitor
        
        for i, sub in enumerate(plan):
            # Phase 39: Autonomous Compute Steering
            # Identify the best node based on thermal efficiency and VRAM availability
            peer_url = await compute_monitor.get_best_node_for_task(required_vram_gb=4.0)
            
            if peer_url == "local":
                # Use default local router if steering suggests local or fails
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
        
        # 1. Execute sub-task to generate a mutation proposal
        # In a real mesh, we call the peer's /api/tasks/execute
        await asyncio.sleep(2) 
        proposal = {
            "path": sub.get("files", ["unknown"])[0],
            "content": "Proposed content change...",
            "rationale": sub.get("description", "Routine refactor"),
            "requester": f"swarm_worker_{index}"
        }

        # 2. Consensus Round (Phase 36)
        # If the task is a 'mutation' (e.g. refactor), require consensus
        if sub.get("type") == "mutation":
            from core.collaboration.consensus import consensus_manager
            from core.agents.base_agent import BaseAgent
            from core.context.manager import ContextManager
            
            # Spawn reviewers (Logic-tier brains)
            reviewers = [
                BaseAgent(None, ContextManager(), model="qwen2.5-coder:32b"),
                BaseAgent(None, ContextManager(), model="qwen2.5-coder:14b")
            ]
            
            passed = await consensus_manager.evaluate_mutation(proposal, reviewers, swarm.id)
            if not passed:
                log.error("swarm.consensus_failed", swarm_id=swarm.id, index=index)
                swarm.results[index] = {"status": "rejected", "summary": "Consensus not reached."}
                return

        # 3. Apply mutation (if passed or not required)
        swarm.results[index] = {"status": "success", "summary": f"Completed {sub['title']} using {model}"}

swarm_manager = SwarmManager()
