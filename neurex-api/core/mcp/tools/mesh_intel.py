"""
core/mcp/tools/mesh_intel.py
Mesh-awareness tools for agentic swarm intelligence.
"""
import os
import structlog
from core.infrastructure.mesh import mesh_router

log = structlog.get_logger()

async def get_mesh_topology() -> str:
    """
    Returns the current state of the federated AI mesh.
    Includes active peers, their VRAM, latency, and current task queue depth.
    Agents can use this to understand where their inference is being routed.
    """
    peers = mesh_router.peers
    if not peers:
        return "Local Node Only: No remote peers connected to the mesh."
        
    summary = ["Active Neurex Swarm:"]
    for url, peer in peers.items():
        status_icon = "🟢" if peer.status == "online" else "🔴"
        summary.append(
            f"{status_icon} {peer.name or url} | "
            f"VRAM: {peer.vram_gb}GB | "
            f"Latency: {peer.latency_ms}ms | "
            f"Queue: {peer.queue_depth}"
        )
        
    return "\n".join(summary)

async def check_peer_suitability(model_name: str) -> str:
    """
    Check which node in the mesh is best suited for a specific model.
    """
    best_url = await mesh_router.get_best_inference_node(model_name)
    if "ollama_proxy" in best_url:
        return f"Model '{model_name}' will be routed to the Neurex Mesh for optimal performance."
    return f"Model '{model_name}' will be executed locally."
