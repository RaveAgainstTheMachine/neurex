
import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_lifespan_boot_concurrency(integration_client: AsyncClient):
    """
    Verifies that the FastAPI lifespan can boot all real daemons
    without deadlocking or crashing.
    """
    response = await integration_client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    
    # Check that sentinel was started and is tracking itself (if applicable)
    # We can ping an internal API to ensure the server is fully alive
    response = await integration_client.get("/api/infra/status")
    assert response.status_code == 200
