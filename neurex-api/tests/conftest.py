"""
Shared pytest fixtures for Neurex API tests.
"""

from __future__ import annotations

import asyncio
import os
from unittest.mock import AsyncMock, patch

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlmodel import SQLModel
from sqlmodel.ext.asyncio.session import AsyncSession

# Set test environment BEFORE importing app modules
os.environ["TESTING"] = "1"
os.environ["WORKSPACE_PATH"] = "/tmp/neurex-test-workspace"
os.environ["OLLAMA_BASE_URL"] = "http://localhost:11434"
os.environ["DATABASE_URL"] = "sqlite+aiosqlite:///test_neurex.db"


@pytest.fixture(scope="session")
def event_loop():
    """Use a single event loop for all tests."""
    loop = asyncio.new_event_loop()
    yield loop
    # Dispose of SQLModel engine cleanly before closing loop
    from core.task_graph import engine
    async def dispose_engine():
        await engine.dispose()
    loop.run_until_complete(dispose_engine())
    loop.close()


@pytest_asyncio.fixture
async def db_session():
    """Provide a clean async DB session for each test."""
    from core.task_graph import engine

    async with engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.create_all)

    session = AsyncSession(engine, expire_on_commit=False)
    try:
        yield session
    finally:
        await session.close()

    async with engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.drop_all)


@pytest_asyncio.fixture
async def test_client():
    """Provide an httpx AsyncClient bound to the FastAPI app.

    Background lifespan services (Ollama checks, watchers, etc.) are
    mocked out so tests don't need a running infrastructure stack.
    """
    # Patch heavy lifespan dependencies
    with (
        patch("core.memory.worker.MemoryWorker.start", new_callable=AsyncMock),
        patch(
            "core.infrastructure.distributed.distributed_manager.start_rpc_server",
            new_callable=AsyncMock,
        ),
        patch(
            "core.infrastructure.firewall.firewall_manager.check_startup", new_callable=AsyncMock
        ),
        patch(
            "core.infrastructure.firewall.firewall_manager.start_sentinel", new_callable=AsyncMock
        ),
        patch("core.infrastructure.mesh.mesh_router.start_monitoring", new_callable=AsyncMock),
        patch("core.observability.service_sentinel.sentinel.start", new_callable=AsyncMock),
        patch(
            "core.observability.ci_healer.ci_healer.check_pipeline_health", new_callable=AsyncMock
        ),
        patch("core.observability.flight_recorder.flush_decisions", new_callable=AsyncMock),
        patch(
            "core.languages.lsp_manager.lsp_manager.initialize_workspace", new_callable=AsyncMock
        ),
        patch(
            "core.observability.dependency_watch.dependency_watch.start_background_watch",
            new_callable=AsyncMock,
        ),
        patch(
            "core.security.sentinel.security_sentinel.start_background_scan",
            new_callable=AsyncMock,
        ),
        patch(
            "core.infrastructure.manager.InfrastructureManager._is_process_running",
            return_value=True,
        ),
    ):
        from main import app

        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            yield client


@pytest.fixture
def mock_ollama_stream():
    """Return a mock that simulates Ollama streaming responses."""

    async def _mock_stream(*args, **kwargs):
        yield {"type": "token", "text": "Hello "}
        yield {"type": "token", "text": "world!"}
        yield {"type": "done", "full_text": "Hello world!"}

    return _mock_stream


@pytest.fixture
def sample_workspace(tmp_path):
    """Create a minimal workspace directory for file operation tests."""
    ws = tmp_path / "workspace"
    ws.mkdir()
    (ws / "hello.py").write_text("print('hello')\n")
    (ws / "src").mkdir()
    (ws / "src" / "main.py").write_text("def main():\n    pass\n")
    return ws
