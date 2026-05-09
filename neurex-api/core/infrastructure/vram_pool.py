"""
core/infrastructure/vram_pool.py
Phase 47: Neural Hardware Virtualization (VRAM Over-Provisioning)
Implements virtualized Mesh-wide VRAM pooling and neural resource orchestration.
Enables treatement of federated hardware as a single unified neural compute pool.
"""
import asyncio
from typing import Any

import structlog

from core.infrastructure.mesh import mesh_router

log = structlog.get_logger()

class VRAMShard:
    def __init__(self, node_id: str, capacity_gb: float):
        self.node_id = node_id
        self.capacity_gb = capacity_gb
        self.used_gb = 0.0
        self.status = "online"

class VirtualVRAMPool:
    def __init__(self):
        self.shards: dict[str, VRAMShard] = {}
        self.pool_lock = asyncio.Lock()
        self.total_capacity_gb = 0.0

    async def synchronize_mesh_resources(self):
        """Discovers peer nodes and aggregates their VRAM into the virtual pool."""
        from core.infrastructure.manager import InfrastructureManager
        infra = InfrastructureManager()
        local_vram = infra.get_system_vram()
        
        async with self.pool_lock:
            active_peers = [p for p in mesh_router.peers.values() if p.status == "online"]
            
            new_shards = {}
            total = local_vram
            
            # Add Local Node
            new_shards["local"] = VRAMShard(node_id="local", capacity_gb=local_vram)
            
            for peer in active_peers:
                capacity = getattr(peer, "vram_gb", 24.0)
                new_shards[peer.url] = VRAMShard(node_id=peer.url, capacity_gb=capacity)
                total += capacity
            
            self.shards = new_shards
            self.total_capacity_gb = total
            
        log.info("vram_pool.mesh_synchronized", 
                 total_nodes=len(self.shards), 
                 total_vram_gb=f"{self.total_capacity_gb:.2f}")

    def allocate_vram(self, required_gb: float) -> list[dict[str, Any]] | None:
        """
        Allocates VRAM from the virtual pool, potentially sharding across nodes.
        Returns a plan for which nodes will host which context/model shards.
        """
        if required_gb > self.total_capacity_gb:
            log.warning("vram_pool.insufficient_capacity", requested=required_gb, available=self.total_capacity_gb)
            return None

        # Simple greedy allocation for now
        allocation_plan = []
        remaining = required_gb
        
        # Sort shards by available capacity (descending) to minimize sharding overhead
        sorted_shards = sorted(self.shards.values(), key=lambda s: s.capacity_gb - s.used_gb, reverse=True)
        
        for shard in sorted_shards:
            available = shard.capacity_gb - shard.used_gb
            if available <= 0:
                continue
                
            sharded_amount = min(remaining, available)
            allocation_plan.append({
                "node_id": shard.node_id,
                "allocated_gb": sharded_amount
            })
            
            remaining -= sharded_amount
            if remaining <= 0:
                break
                
        if remaining > 0:
            return None # Should not happen if check passed
            
        log.info("vram_pool.allocation_successful", requested_gb=required_gb, nodes_utilized=len(allocation_plan))
        return allocation_plan

    def release_vram(self, plan: list[dict[str, Any]]):
        """Releases allocated VRAM back into the pool."""
        for entry in plan:
            node_id = entry["node_id"]
            if node_id in self.shards:
                self.shards[node_id].used_gb = max(0.0, self.shards[node_id].used_gb - entry["allocated_gb"])

vram_pool = VirtualVRAMPool()
