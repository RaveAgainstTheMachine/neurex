"""
tests/test_benchmarks.py
Tests for the simulation benchmarks API endpoints (/run and /status).
"""

import asyncio
from unittest.mock import AsyncMock, patch

import pytest


@pytest.fixture(autouse=True)
def override_auth():
    from api.routes.auth import get_current_user
    from core.task_graph import User, UserRole
    from main import app

    mock_user = User(username="test_admin", role=UserRole.ADMIN)

    async def mock_get_current_user():
        return mock_user

    app.dependency_overrides[get_current_user] = mock_get_current_user
    yield
    app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_benchmark_flow(test_client):
    """Verify triggering a benchmark and tracking its status/parsing."""
    # Reset state to idle if needed (for clean isolation)
    from api.routes.benchmarks import _LOCK, BENCHMARK_STATE
    async with _LOCK:
        BENCHMARK_STATE["status"] = "idle"
        BENCHMARK_STATE["results"] = []
        BENCHMARK_STATE["log"] = []
        BENCHMARK_STATE["score"] = "0/0"
        BENCHMARK_STATE["percentage"] = 0

    mock_process = AsyncMock()
    mock_process.stdout = AsyncMock()
    mock_process.stderr = AsyncMock()

    # UTF-8 representations:
    # ✅ PASS -> \xe2\x9c\x85 PASS
    # ❌ FAIL -> \xe2\x9d\x8c FAIL
    outputs = [
        b"\xf0\x9f\xa7\xaa Running Neurex Simulation Benchmarks\n",
        b"  smoke-hello                        \xe2\x9c\x85 PASS  (1.23s)\n",
        b"  py-fibonacci                       \xe2\x9d\x8c FAIL  (Missing: fibonacci.py)\n",
        b"Score: 1/2  (50%)\n",
        b""  # EOF
    ]

    mock_process.stdout.readline.side_effect = outputs
    mock_process.stderr.read.return_value = b""
    mock_process.wait = AsyncMock(return_value=0)

    with patch("asyncio.create_subprocess_exec", return_value=mock_process) as mock_exec:
        # 1. Start benchmark
        run_response = await test_client.post("/api/benchmarks/run")
        assert run_response.status_code == 200
        assert run_response.json()["status"] == "ok"

        # Wait for the background task to complete (or time out)
        for _ in range(20):
            await asyncio.sleep(0.05)
            status_response = await test_client.get("/api/benchmarks/status")
            status_data = status_response.json()
            if status_data["status"] in ["completed", "failed"]:
                break
        else:
            pytest.fail("Benchmark background task did not finish in time")

        # 2. Assert correct state has been parsed & saved
        assert status_data["status"] == "completed"
        assert status_data["score"] == "1/2"
        assert status_data["percentage"] == 50
        assert len(status_data["results"]) == 2

        case1, case2 = status_data["results"]
        assert case1["id"] == "smoke-hello"
        assert case1["passed"] is True
        assert case1["duration_s"] == 1.23

        assert case2["id"] == "py-fibonacci"
        assert case2["passed"] is False
        assert "Missing: fibonacci.py" in case2["details"]

        # Ensure correct command was executed
        mock_exec.assert_called_once()
        args, kwargs = mock_exec.call_args
        assert "run_evals.py" in str(args[1])


@pytest.mark.asyncio
async def test_run_benchmark_already_running(test_client):
    """Ensure POST /run fails if a benchmark is currently running."""
    from api.routes.benchmarks import _LOCK, BENCHMARK_STATE
    async with _LOCK:
        BENCHMARK_STATE["status"] = "running"

    try:
        response = await test_client.post("/api/benchmarks/run")
        assert response.status_code == 400
        assert "already running" in response.json()["detail"]
    finally:
        async with _LOCK:
            BENCHMARK_STATE["status"] = "idle"
