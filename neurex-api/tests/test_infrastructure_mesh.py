from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from core.infrastructure.mesh import (
    MeshRouter,
    PeerNode,
    ResourcePredictor,
)


@pytest.fixture
def router():
    with patch("core.infrastructure.mesh.PEERS_FILE") as mock_file:
        mock_file.exists.return_value = False
        return MeshRouter()

def test_peer_node_telemetry():
    peer = PeerNode("http://test", "token", "Test")
    peer.record_telemetry({"cpu_percent": 50.0, "vram_gb": 4.0, "queue_depth": 2})
    assert len(peer.history) == 1
    assert peer.history[0]["cpu"] == 50.0

def test_resource_predictor():
    history = [
        {"cpu": 10.0, "queue": 0},
        {"cpu": 20.0, "queue": 1},
        {"cpu": 30.0, "queue": 2},
    ]
    load = ResourcePredictor.predict_future_load(history)
    assert load > 0.0

@pytest.mark.asyncio
async def test_mesh_router_add_remove_peer(router):
    with patch.object(router, "check_health", new_callable=AsyncMock) as mock_health:
        with patch.object(router, "_save_peers"):
            assert router.add_peer("http://test", "token", "Test") is True
            assert len(router.peers) == 1
            
            # Add again returns false
            assert router.add_peer("http://test", "token", "Test") is False
            
            router.remove_peer("http://test")
            assert len(router.peers) == 0

@pytest.mark.asyncio
async def test_mesh_router_check_health(router):
    router.peers["http://test"] = PeerNode("http://test", "token", "Test")
    
    with patch.object(router._client, "get", new_callable=AsyncMock) as mock_get:
        mock_resp = MagicMock()
        mock_resp.json.return_value = {
            "metrics": {"vram_gb": 8.0, "cpu_percent": 10.0},
            "local_models": [{"name": "llama3"}],
            "queue_depth": 1
        }
        mock_get.return_value = mock_resp
        
        with patch.object(router, "_save_peers"):
            await router.check_health("http://test")
            peer = router.peers["http://test"]
            assert peer.status == "online"
            assert peer.vram_gb == 8.0
            assert peer.cpu_percent == 10.0
            assert len(peer.models) == 1

@pytest.mark.asyncio
async def test_mesh_router_check_health_offline(router):
    router.peers["http://test"] = PeerNode("http://test", "token", "Test")
    
    with patch.object(router._client, "get", side_effect=Exception("network error")):
        with patch.object(router, "_save_peers"):
            await router.check_health("http://test")
            peer = router.peers["http://test"]
            assert peer.status == "offline"

@pytest.mark.asyncio
async def test_mesh_router_get_best_inference_node(router):
    with patch("core.infrastructure.manager.infrastructure_manager.get_system_metrics", return_value={"vram_gb": 4.0, "cpu_percent": 50.0}):
        with patch("core.infrastructure.manager.infrastructure_manager.get_installed_models", new_callable=AsyncMock, return_value=[{"name": "llama3"}]):
            router.peers["http://peer1"] = PeerNode("http://peer1", "token", "Peer1")
            router.peers["http://peer1"].status = "online"
            router.peers["http://peer1"].vram_gb = 24.0
            router.peers["http://peer1"].cpu_percent = 10.0
            router.peers["http://peer1"].models = [{"name": "llama3"}]
            router.peers["http://peer1"].queue_depth = 0
            
            node = await router.get_best_inference_node("llama3")
            assert "peer1" in node or "localhost" in node

@pytest.mark.asyncio
async def test_mesh_router_resolve_model_and_node(router):
    with patch.object(router, "get_best_inference_node", new_callable=AsyncMock, return_value="http://peer1/api"):
        with patch("core.infrastructure.manager.infrastructure_manager.get_installed_models", new_callable=AsyncMock, return_value=[{"name": "llama3"}]):
            router.peers["http://peer1"] = PeerNode("http://peer1", "token", "Peer1")
            router.peers["http://peer1"].status = "online"
            router.peers["http://peer1"].models = [{"name": "qwen2.5-coder"}]
            
            node_url, resolved_model, warning = await router.resolve_model_and_node("llama3", "coder")
            assert node_url == "http://peer1/api"
            assert resolved_model == "llama3"

@pytest.mark.asyncio
async def test_mesh_router_sync_with_peer(router):
    router.peers["http://peer1"] = PeerNode("http://peer1", "token", "Peer1")
    router.peers["http://peer1"].status = "online"
    
    with patch.object(router._client, "get", new_callable=AsyncMock) as mock_get:
        mock_resp = MagicMock()
        mock_resp.json.return_value = {
            "manifest": {"test.py": {"hash": "abc", "mtime": 100, "size": 10}}
        }
        mock_get.return_value = mock_resp
        
        with patch("core.infrastructure.mesh.generate_local_manifest", return_value={"local.py": {"hash": "def", "mtime": 200, "size": 20}}):
            with patch.object(router._client, "post", new_callable=AsyncMock) as mock_post:
                mock_post_resp = MagicMock()
                mock_post.return_value = mock_post_resp
                
                with patch("pathlib.Path.read_bytes", return_value=b"data"):
                    await router.sync_with_peer("http://peer1")
                    assert mock_get.call_count >= 1

@pytest.mark.asyncio
async def test_mesh_router_start_monitoring(router):
    # just test it does not crash when started
    with patch("asyncio.sleep", new_callable=AsyncMock, side_effect=Exception("StopLoop")):
        with patch("core.infrastructure.vram_pool.vram_pool.synchronize_mesh_resources", new_callable=AsyncMock):
            with pytest.raises(Exception, match="StopLoop"):
                await router.start_monitoring(1)
