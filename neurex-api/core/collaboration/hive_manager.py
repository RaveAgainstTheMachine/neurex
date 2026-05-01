"""
core/collaboration/hive_manager.py
Neural Mesh Hive-Mind (Phase 44).
Coordinates multiple swarms on shared planning blueprints via sharding and locking.
"""
from __future__ import annotations
import asyncio
import structlog
from typing import List, Dict, Any, Set
from core.context.global_memory import global_memory
from core.observability.flight_recorder import record_decision

log = structlog.get_logger()

class HiveManager:
    def __init__(self):
        # Local locks for paths being mutated: path -> task_id
        self.path_locks: Dict[str, str] = {}
        # Active blueprints: id -> list of shards
        self.active_blueprints: Dict[str, List[Dict[str, Any]]] = {}
        # Phase 44.1: O(1) Shard Lookup
        self.shards_by_id: Dict[str, Dict[str, Any]] = {}

    async def shard_blueprint(self, blueprint_id: str, blueprint: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Breaks a massive HyperPlan blueprint into parallelizable shards."""
        log.info("hive.sharding_blueprint", id=blueprint_id)
        
        steps = blueprint.get("steps", [])
        shards = []
        
        for step in steps:
            shard_id = f"{blueprint_id}_s{len(shards)}"
            shard = {
                "blueprint_id": blueprint_id,
                "shard_id": shard_id,
                "step": step,
                "status": "pending",
                "locked_paths": step.get("target_paths", [])
            }
            shards.append(shard)
            self.shards_by_id[shard_id] = shard
            
        self.active_blueprints[blueprint_id] = shards
        await record_decision("hive_sharding", "blueprint_sharded", blueprint_id, f"Created {len(shards)} shards.")
        return shards

    async def claim_shard(self, task_id: str, shard_id: str) -> bool:
        """Claims a shard using O(1) lookup and locks its target paths."""
        target_shard = self.shards_by_id.get(shard_id)
        
        if not target_shard or target_shard["status"] != "pending":
            return False

        # Verify path locks
        for path in target_shard["locked_paths"]:
            if path in self.path_locks and self.path_locks[path] != task_id:
                log.warning("hive.path_locked", path=path, owner=self.path_locks[path])
                return False

        # Apply locks
        for path in target_shard["locked_paths"]:
            self.path_locks[path] = task_id
            
        target_shard["status"] = "executing"
        target_shard["owner"] = task_id
        
        await global_memory.add_pointer(f"lock:{shard_id}", f"Claimed by {task_id}")
        return True

    def release_shard(self, task_id: str, shard_id: str):
        """Releases locks associated with a shard via fast lookup."""
        target_shard = self.shards_by_id.get(shard_id)
        if target_shard and target_shard.get("owner") == task_id:
            for path in target_shard["locked_paths"]:
                if self.path_locks.get(path) == task_id:
                    del self.path_locks[path]
            target_shard["status"] = "completed"
            # Cleanup lookup if blueprint is done (simplified logic)
            # del self.shards_by_id[shard_id] 

hive_manager = HiveManager()
