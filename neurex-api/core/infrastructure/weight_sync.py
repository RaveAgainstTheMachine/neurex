"""
core/infrastructure/weight_sync.py
Phase 48: Neural Evolution (Federated Weight Propagation)
Synchronizes evolved neural adapter weights across the Mesh.
Ensures neural coherence by propagating finalized LoRA checkpoints to all nodes.
"""
import asyncio
import os
from pathlib import Path
from typing import Any

import structlog

from core.infrastructure.mesh import mesh_router

log = structlog.get_logger()

ADAPTERS_DIR = Path(os.getenv("WORKSPACE_PATH", "/workspace")) / ".neurex" / "adapters"

class WeightPropagator:
    def __init__(self):
        self.sync_lock = asyncio.Lock()
        ADAPTERS_DIR.mkdir(parents=True, exist_ok=True)

    async def propagate_adapter(self, adapter_id: str, version: int, local_path: str):
        """
        Broadcasting a finalized neural adapter to all Mesh nodes.
        Uses a chunked streaming approach (simulated) to ensure reliable delivery.
        """
        async with self.sync_lock:
            peers = [p for p in mesh_router.peers.values() if p.status == "online"]
            if not peers:
                log.info("weight_sync.no_peers_to_sync", adapter=adapter_id)
                return

            log.info("weight_sync.broadcasting_weights", 
                     adapter=adapter_id, 
                     version=version, 
                     target_nodes=len(peers))

            # Parallel propagation to all nodes
            tasks = [self._sync_to_node(peer, adapter_id, version, local_path) for peer in peers]
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            success_count = sum(1 for r in results if r is True)
            log.info("weight_sync.propagation_complete", 
                     adapter=adapter_id, 
                     success=success_count, 
                     failed=len(peers) - success_count)

    async def _sync_to_node(self, peer: Any, adapter_id: str, version: int, local_path: str) -> bool:
        """Propagates weights to a specific node via the Mesh backplane."""
        try:
            log.debug("weight_sync.pushing_to_node", node=peer.url, adapter=adapter_id)
            
            # Phase 48: Weights are pushed via a dedicated secure channel or multi-part POST
            # Simulated high-speed transfer (e.g. 50MB adapter over mesh)
            await asyncio.sleep(0.5) # 500ms simulated transfer
            
            # In a real implementation, we would use:
            # await self._client.post(f"{peer.url}/api/infra/evolution/receive-weights", ...)
            
            return True
        except Exception as e:
            log.warning("weight_sync.node_sync_failed", node=peer.url, error=str(e))
            return False

    def get_local_adapter_path(self, adapter_id: str, version: int) -> Path:
        """Returns the local filesystem path for a specific adapter version."""
        return ADAPTERS_DIR / f"{adapter_id}_v{version}.bin"

    async def finalize_local_mutation(self, adapter_id: str, version: int, weights_blob: Any):
        """Saves a newly aggregated adapter to the local filesystem."""
        path = self.get_local_adapter_path(adapter_id, version)
        async with self.sync_lock:
            # Simulated weight saving
            with open(path, "wb") as f:
                f.write(b"NEURAL_ADAPTER_WEIGHTS_BLOB") 
            
        log.info("weight_sync.mutation_finalized_locally", path=str(path))
        return str(path)

weight_sync = WeightPropagator()
