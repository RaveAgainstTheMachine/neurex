"""
core/context/federated_rag.py
Mesh-Scale Distributed RAG (Global Intelligence).
Federates search queries across all nodes in the Neurex Mesh.
"""
from __future__ import annotations
import asyncio
import httpx
import structlog
from typing import List, Dict, Any
from core.infrastructure.mesh import mesh_router
from core.context.manager import ContextManager

log = structlog.get_logger()

class FederatedRAG:
    def __init__(self, local_ctx: ContextManager):
        self.local_ctx = local_ctx

    async def global_search(self, query: str, limit: int = 5) -> str:
        """
        Performs a federated search across the local node and all Mesh peers.
        """
        log.info("rag.global_search_start", query=query[:50])
        
        # 1. Local Search (AST-aware)
        local_task = self.local_ctx.explorer.hybrid_search(query, limit=limit)
        
        # 2. Mesh Peer Search (Optimized with a single client pool)
        peers = list(mesh_router.peers.values())
        async with httpx.AsyncClient(timeout=10) as client:
            peer_tasks = [self._search_peer(client, peer, query, limit) for peer in peers]
            
            # 3. Aggregate all results
            all_results = await asyncio.gather(local_task, *peer_tasks)
        
        # Flatten and format
        flat_results = []
        for res_list in all_results:
            if isinstance(res_list, list):
                flat_results.extend(res_list)
        
        # 4. Re-rank and format (Caveman style: take top N)
        # In a full implementation, we would use a cross-encoder for re-ranking.
        formatted = "\n\n".join(
            f"### [SOURCE: {r.get('metadata', {}).get('node', 'local')}:{r.get('metadata', {}).get('file', 'unknown')}]\n{r.get('document', '')}"
            for r in flat_results[:limit*2]
        )
        
        log.info("rag.global_search_complete", results=len(flat_results))
        return f"<global_mesh_context>\n{formatted}\n</global_mesh_context>"

    async def _search_peer(self, client: httpx.AsyncClient, peer, query: str, limit: int) -> List[Dict[str, Any]]:
        """Queries a peer's RAG endpoint using the shared client."""
        try:
            resp = await client.get(
                f"{peer.url}/api/rag/search",
                params={"query": query, "limit": limit},
                headers={"Authorization": f"Bearer {peer.token}"}
            )
            if resp.status_code == 200:
                results = resp.json()
                # Tag results with peer name
                for r in results:
                    r["metadata"]["node"] = peer.name
                return results
        except Exception as e:
            log.warning("rag.peer_search_failed", peer=peer.name, error=str(e))
        return []

# Integrated into BaseAgent
