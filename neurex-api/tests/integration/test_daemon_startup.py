
import pytest
from httpx import ASGITransport, AsyncClient


@pytest.fixture
def override_ports(monkeypatch):
    # Use random/high ports to avoid conflicting with actual running dev instances
    monkeypatch.setenv("RPC_PORT", "50052")
    monkeypatch.setenv("FIREWALL_PORT", "8444")
    monkeypatch.setenv("MESH_PORT", "9001")
    monkeypatch.setenv("ENABLE_AGENT_INTERNET", "false")

@pytest.mark.asyncio
async def test_daemon_startup(override_ports, db_session):
    """
    Tests that the FastAPI lifespan can start up and shut down all background 
    daemons (MemoryWorker, Sentinel, RPC, Firewall, etc.) without deadlocks or errors.
    """
    from main import app
    
    # We use ASGITransport directly, triggering the app's full lifespan natively.
    transport = ASGITransport(app=app)
    
    # The 'with' block triggers lifespan startup
    try:
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            # If we reached here, startup succeeded.
            # Make a basic health check to ensure the event loop is responsive.
            resp = await client.get("/health")
            assert resp.status_code == 200
            data = resp.json()
            assert data["status"] == "ok"
    except Exception as e:
        pytest.fail(f"App lifespan failed to start/stop: {e}")
