"""
tests/test_smoke_evals.py
Pytest integration for the Neurex smoke evaluation cases.
"""

from __future__ import annotations

from unittest.mock import AsyncMock, patch

import pytest
from fastapi.testclient import TestClient

from main import app


@pytest.mark.asyncio
async def test_smoke_eval_cases():
    """
    Runs the defined smoke eval cases against a mocked Orchestrator and WebSocket client
    to guarantee the evaluation harness logic and websocket routing are fully wired.
    """
    from eval.run_evals import EVAL_CASES

    # Filter to smoke cases only
    smoke_cases = [c for c in EVAL_CASES if c["tag"] == "smoke"]
    assert len(smoke_cases) >= 3  # Ensure our new case is also included

    with (
        patch("core.memory.worker.MemoryWorker.start", new_callable=AsyncMock),
        patch("core.infrastructure.distributed.distributed_manager.start_rpc_server", new_callable=AsyncMock),
        patch("core.infrastructure.firewall.firewall_manager.check_startup", new_callable=AsyncMock),
        patch("core.infrastructure.firewall.firewall_manager.start_sentinel", new_callable=AsyncMock),
        patch("core.infrastructure.mesh.mesh_router.start_monitoring", new_callable=AsyncMock),
        patch("core.observability.service_sentinel.sentinel.start", new_callable=AsyncMock),
        patch("core.observability.ci_healer.ci_healer.check_pipeline_health", new_callable=AsyncMock),
        patch("core.observability.flight_recorder.flush_decisions", new_callable=AsyncMock),
        patch("core.languages.lsp_manager.lsp_manager.initialize_workspace", new_callable=AsyncMock),
        patch("core.infrastructure.manager.InfrastructureManager._is_process_running", return_value=True),
        patch("api.websocket._authenticate", new_callable=AsyncMock) as mock_auth,
        patch("core.orchestrator.Orchestrator.run") as mock_run,
        patch("core.orchestrator.Orchestrator.resume") as mock_resume,
    ):
        mock_auth.return_value = True

        for case in smoke_cases:
            # Mock Orchestrator.run to yield plan_ready
            async def mock_run_gen(*args, **kwargs):
                yield {"event": "token", "data": f"Evaluating: {case['prompt']}"}
                yield {"event": "plan_ready", "data": {"graph_id": f"graph-{case['id']}"}}
            mock_run.side_effect = mock_run_gen

            # Mock Orchestrator.resume to yield done
            async def mock_resume_gen(*args, **kwargs):
                yield {"event": "token", "data": "Executing smoke eval task..."}
                yield {"event": "done", "data": {"graph_id": f"graph-{case['id']}"}}
            mock_resume.side_effect = mock_resume_gen

            def wait_for_event(ws, event_type):
                while True:
                    ev = ws.receive_json()
                    if ev.get("event") == event_type:
                        return ev

            # Run evaluation case through websocket test client
            with TestClient(app) as client:
                url = f"/ws/{case['id']}?token=mocked-token"
                with client.websocket_connect(url) as websocket:
                    websocket.send_json({"type": "message", "content": case["prompt"]})

                    # Read token event
                    ev1 = wait_for_event(websocket, "token")
                    assert case["prompt"] in ev1["data"]

                    # Read plan_ready event
                    ev2 = wait_for_event(websocket, "plan_ready")
                    graph_id = ev2["data"]["graph_id"]
                    assert graph_id == f"graph-{case['id']}"

                    # Approve plan
                    websocket.send_json({"type": "approve_plan", "graph_id": graph_id})

                    # Read resume token event
                    ev3 = wait_for_event(websocket, "token")
                    assert "Executing" in ev3["data"]

                    # Read done event
                    ev4 = wait_for_event(websocket, "done")
                    assert ev4["data"]["graph_id"] == graph_id
