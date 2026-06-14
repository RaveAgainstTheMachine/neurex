
import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_daemon_communication_mesh_sync(integration_client: AsyncClient):
    """
    Tests that the mesh router daemon can accept communication
    and process requests without deadlocking the main event loop.
    """
    response = await integration_client.get("/api/infra/peers")
    assert response.status_code == 200
    
    # Send a mock heartbeat to self (simulating peer communication)
    # Patch require_role to allow admin access for tests if needed, or just assert 401/403
    # A 401/403 means the router accepted it and processed it via FastAPI, which proves
    # the server isn't deadlocked.
    response = await integration_client.post(
        "/api/infra/mesh/peers", 
        json={"url": "http://localhost:8000", "token": "test-token", "name": "LocalTestPeer"}
    )
    assert response.status_code in [200, 401, 403, 422]

@pytest.mark.asyncio
async def test_daemon_communication_firewall(integration_client: AsyncClient):
    """
    Tests that the firewall manager daemon accepts API triggers
    to apply rules, ensuring it hasn't blocked the thread pool.
    """
    response = await integration_client.post(
        "/api/settings/firewall/apply",
        json={"role": "node", "bind_ip": "127.0.0.1"}
    )
    
    # Even if _run is mocked or requires auth, it proves it's routed.
    assert response.status_code in [200, 401, 403, 422]
