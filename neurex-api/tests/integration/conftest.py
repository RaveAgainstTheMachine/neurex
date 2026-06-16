"""
Integration tests for Neurex API.
This directory contains tests that do NOT use the heavily mocked test_client fixture
from the parent conftest.py, allowing for true end-to-end integration of background daemons.
"""
import asyncio
import os
from unittest.mock import AsyncMock, patch

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient

# Provide integration-specific env vars BEFORE imports
os.environ["TESTING"] = "1"
os.environ["WORKSPACE_PATH"] = "/tmp/neurex-integration-workspace"
os.environ["DATABASE_URL"] = "sqlite+aiosqlite:///test_neurex_integration.db"

@pytest.fixture(scope="session")
def event_loop():
    loop = asyncio.new_event_loop()
    yield loop
    try:
        from core.task_graph import engine
        async def dispose_engine():
            await engine.dispose()
        loop.run_until_complete(dispose_engine())
    except Exception:
        pass
    loop.close()

@pytest_asyncio.fixture
async def integration_client():
    """
    Test client that uses the REAL lifespan instead of mocking everything.
    We only mock the heaviest system dependencies (like Ollama startup and real firewall commands)
    so the tests don't require root or heavy GPU resources, but all daemon loops run concurrently.
    """
    with (
        patch("core.infrastructure.firewall._run", return_value=(0, "")),
        patch("core.infrastructure.manager.InfrastructureManager._is_process_running", return_value=True),
        patch("core.languages.lsp_manager.lsp_manager.initialize_workspace", new_callable=AsyncMock),
        patch("core.infrastructure.distributed.distributed_manager.start_rpc_server", new_callable=AsyncMock),
        patch("core.observability.dependency_watch.dependency_watch.start_background_watch", new_callable=AsyncMock),
    ):
        from main import app
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            yield client
