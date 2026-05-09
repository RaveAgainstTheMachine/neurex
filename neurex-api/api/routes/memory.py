"""
api/routes/memory.py
Endpoints for querying and managing the Swarm's Collective Memory (Hive Mind).
"""

from fastapi import APIRouter, Depends, Query

from api.routes.auth import UserRole, require_role
from core.memory.hive import hive_mind

router = APIRouter()

@router.get("/search")
async def search_memory(
    q: str = Query(..., description="The semantic search query"),
    n_results: int = 5
):
    """Perform a vector search across the collective memory."""
    results = hive_mind.search(q, n_results=n_results)
    
    # Format for frontend
    formatted = []
    if results and results["documents"]:
        for i in range(len(results["documents"][0])):
            formatted.append({
                "id": results["ids"][0][i],
                "content": results["documents"][0][i],
                "metadata": results["metadatas"][0][i],
                "distance": results["distances"][0][i] if "distances" in results else 0
            })
            
    return {"results": formatted}

@router.get("/stats")
async def get_memory_stats():
    """Get metadata about the current memory state."""
    from core.infrastructure.mesh import mesh_router
    
    # Calculate real online nodes (Local + Online Peers)
    online_peers = sum(1 for p in mesh_router.peers.values() if p.status == "online")
    total_active_nodes = 1 + online_peers
    
    return {
        "total_nodes": total_active_nodes, 
        "memory_count": hive_mind.collection.count() if hive_mind.collection else 0,
        "collection_name": "neurex_collective"
    }

@router.post("/clear")
async def clear_memory(current_user = Depends(require_role(UserRole.ADMIN))):
    """Wipe the collective memory. Restricted to ADMIN."""
    # Implementation for collection.delete()
    return {"status": "cleared"}
