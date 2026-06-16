from unittest.mock import AsyncMock, patch

import pytest

from core.infrastructure.mesh import PeerNode
from core.mcp.tools.mesh_intel import check_peer_suitability, get_mesh_topology


@pytest.mark.asyncio
async def test_get_mesh_topology_empty():
    with patch("core.infrastructure.mesh.mesh_router.peers", {}):
        res = await get_mesh_topology()
        assert "Local Node Only" in res

@pytest.mark.asyncio
async def test_get_mesh_topology_with_peers():
    peer1 = PeerNode("http://peer1", "token1", "PeerOne")
    peer1.status = "online"
    peer1.vram_gb = 16.0
    peer1.latency_ms = 12
    peer1.queue_depth = 0

    peer2 = PeerNode("http://peer2", "token2", "PeerTwo")
    peer2.status = "offline"

    peers = {"http://peer1": peer1, "http://peer2": peer2}

    with patch("core.infrastructure.mesh.mesh_router.peers", peers):
        res = await get_mesh_topology()
        assert "🟢 PeerOne" in res
        assert "VRAM: 16.0GB" in res
        assert "🔴 PeerTwo" in res

@pytest.mark.asyncio
async def test_check_peer_suitability():
    # Case 1: Local routing
    with patch("core.infrastructure.mesh.mesh_router.get_best_inference_node", new_callable=AsyncMock, return_value="http://localhost:11434"):
        res = await check_peer_suitability("model-a")
        assert "executed locally" in res

    # Case 2: Proxy routing
    with patch("core.infrastructure.mesh.mesh_router.get_best_inference_node", new_callable=AsyncMock, return_value="http://peer1/api/infra/ollama_proxy"):
        res = await check_peer_suitability("model-b")
        assert "routed to the Neurex Mesh" in res
