from unittest.mock import AsyncMock, MagicMock, patch

import httpx
import pytest

from core.context.federated_rag import FederatedRAG
from core.infrastructure.mesh import PeerNode


@pytest.mark.asyncio
async def test_federated_rag_global_search_success():
    local_ctx = MagicMock()
    # Case 1: local_ctx has explorer
    mock_explorer = MagicMock()
    mock_explorer.hybrid_search = AsyncMock(return_value=[
        {"metadata": {"file": "local.py"}, "document": "local content"}
    ])
    local_ctx.explorer = mock_explorer

    rag = FederatedRAG(local_ctx)

    # Mock peer nodes
    peer = PeerNode("http://peer1", "token1", "PeerOne")
    peer.status = "online"
    peers = {"http://peer1": peer}

    # Mock response from peer
    mock_response = MagicMock(spec=httpx.Response)
    mock_response.status_code = 200
    mock_response.json.return_value = [
        {"metadata": {"file": "peer.py"}, "document": "peer content"}
    ]

    with patch("core.infrastructure.mesh.mesh_router.peers", peers):
        with patch("httpx.AsyncClient.get", new_callable=AsyncMock, return_value=mock_response):
            res = await rag.global_search("test query", limit=2)
            assert "local content" in res
            assert "peer content" in res
            assert "SOURCE: PeerOne:peer.py" in res

@pytest.mark.asyncio
async def test_federated_rag_global_search_fallback_and_error():
    local_ctx = MagicMock()
    local_ctx.explorer = None
    local_ctx.retrieve = AsyncMock(return_value=[
        {"metadata": {"file": "fallback.py"}, "document": "fallback content"}
    ])

    rag = FederatedRAG(local_ctx)

    # Mock peer node causing exception
    peer = PeerNode("http://peer2", "token2", "PeerTwo")
    peers = {"http://peer2": peer}

    with patch("core.infrastructure.mesh.mesh_router.peers", peers):
        with patch("httpx.AsyncClient.get", new_callable=AsyncMock, side_effect=Exception("Connection failed")):
            res = await rag.global_search("test query", limit=2)
            assert "fallback content" in res
            assert "PeerTwo" not in res
