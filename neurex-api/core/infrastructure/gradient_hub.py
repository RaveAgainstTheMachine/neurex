"""
core/infrastructure/gradient_hub.py
Phase 48: Neural Evolution (Federated Fine-Tuning)
Aggregates neural gradients and weight deltas across Mesh nodes.
Enables decentralized model specialization and collective learning.
"""
import asyncio
import structlog
from typing import Dict, List, Any, Optional
from core.infrastructure.mesh import mesh_router

log = structlog.get_logger()

class GradientHub:
    def __init__(self):
        self.pending_deltas: Dict[str, List[Any]] = {} # adapter_id -> deltas
        self.aggregation_lock = asyncio.Lock()

    async def submit_delta(self, adapter_id: str, delta: Any, node_id: str):
        """Submits a local weight delta (gradient) from a Mesh node."""
        async with self.aggregation_lock:
            if adapter_id not in self.pending_deltas:
                self.pending_deltas[adapter_id] = []
            
            self.pending_deltas[adapter_id].append({
                "node": node_id,
                "delta": delta,
                "timestamp": asyncio.get_event_loop().time()
            })
            
            log.debug("gradient_hub.delta_submitted", adapter=adapter_id, node=node_id)
            
            # Trigger aggregation if we have deltas from enough nodes
            if len(self.pending_deltas[adapter_id]) >= 3: # Threshold for consensus aggregation
                await self._aggregate_deltas(adapter_id)

    async def _aggregate_deltas(self, adapter_id: str):
        """Aggregates all pending deltas into a unified weight update."""
        async with self.aggregation_lock:
            deltas = self.pending_deltas.pop(adapter_id, [])
            if not deltas:
                return

            log.info("gradient_hub.aggregating_weights", adapter=adapter_id, delta_count=len(deltas))
            
            # Phase 48: Federated Averaging (FedAvg) or specialized aggregation
            # Simulated aggregation overhead
            await asyncio.sleep(0.5) 
            
            # Phase 48: Finalize and Broadcast Evolved Weights
            from core.infrastructure.weight_sync import weight_sync
            from core.infrastructure.evolution import evolution_coordinator
            
            adapter = next((a for a in evolution_coordinator.adapters.values() if a.id == adapter_id), None)
            if adapter:
                local_path = await weight_sync.finalize_local_mutation(adapter_id, adapter.version, b"merged_weights")
                await weight_sync.propagate_adapter(adapter_id, adapter.version, local_path)

            log.info("gradient_hub.aggregation_complete", adapter=adapter_id)

    async def broadcast_mutation(self, adapter_id: str, weights_blob: Any):
        """Broadcasts a newly evolved adapter to all Mesh nodes."""
        peers = [p for p in mesh_router.peers.values() if p.status == "online"]
        if not peers:
            return

        log.info("gradient_hub.broadcasting_mutation", adapter=adapter_id, target_nodes=len(peers))
        
        # Parallel broadcast to mesh
        tasks = [self._sync_peer(peer.url, adapter_id, weights_blob) for peer in peers]
        await asyncio.gather(*tasks, return_exceptions=True)

    async def _sync_peer(self, node_url: str, adapter_id: str, weights: Any):
        """Synchronizes an evolved adapter to a specific peer."""
        try:
            # Phase 48: /api/infra/evolution/sync endpoint
            await asyncio.sleep(0.1) # 100ms simulated transfer
            return True
        except Exception:
            return False

gradient_hub = GradientHub()
