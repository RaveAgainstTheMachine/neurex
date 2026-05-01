"""
core/context/global_memory.py
Mesh-Wide Memory (Persistent Global State).
Synchronizes 'Global Sticky Notes' and experience patterns across the Mesh.
"""
from __future__ import annotations
import asyncio
import httpx
import structlog
from typing import List, Dict, Any
from core.infrastructure.mesh import mesh_router
from core.observability.flight_recorder import record_decision

log = structlog.get_logger()

class GlobalMemory:
    def __init__(self):
        # Local cache of global memory pointers
        # key: str, value: {"content": str, "source_node": str, "timestamp": str}
        self.pointers: Dict[str, Dict[str, Any]] = {}
        # Historical success patterns
        self.patterns: List[Dict[str, Any]] = []

    async def add_pointer(self, key: str, content: str, node_id: str = "local"):
        """Adds a local memory pointer and prepares for broadcast."""
        log.info("memory.add_pointer", key=key, node=node_id)
        self.pointers[key] = {
            "content": content,
            "source_node": node_id,
            "timestamp": "2026-05-01T07:08:00Z" # Placeholder
        }
        await record_decision("global_memory", "pointer_added", key, content[:50])
        
        # Broadcast to Mesh (Phase 41)
        asyncio.create_task(self.broadcast_memory())

    async def query_memory(self, query: str) -> str:
        """Searches global memory for relevant context."""
        # Simple keyword search (Caveman style)
        matches = []
        for key, val in self.pointers.items():
            if query.lower() in key.lower() or query.lower() in val["content"].lower():
                matches.append(f"[{val['source_node']}] {key}: {val['content']}")
        
        return "\n".join(matches) if matches else "No matching global memory found."

    async def broadcast_memory(self):
        """Broadcasts local pointers to all Mesh peers."""
        peers = list(mesh_router.peers.values())
        if not peers:
            return

        payload = {"pointers": self.pointers}
        async with httpx.AsyncClient(timeout=5) as client:
            tasks = []
            for peer in peers:
                tasks.append(client.post(f"{peer.url}/api/memory/sync", json=payload))
            
            await asyncio.gather(*tasks, return_exceptions=True)
            log.info("memory.broadcast_complete", peers=len(peers))

    def sync_from_peer(self, peer_id: str, remote_pointers: Dict[str, Dict[str, Any]]):
        """Merges remote pointers into local memory."""
        log.info("memory.sync_from_peer", peer=peer_id, count=len(remote_pointers))
        for key, val in remote_pointers.items():
            # Basic conflict resolution: Source node priority or timestamps
            if key not in self.pointers:
                self.pointers[key] = val

global_memory = GlobalMemory()
