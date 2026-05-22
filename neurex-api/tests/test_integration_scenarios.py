"""
tests/test_integration_scenarios.py
Deep integration tests for the Orchestrator task graph lifecycles.
"""

from __future__ import annotations

from unittest.mock import patch

import pytest
from sqlmodel.ext.asyncio.session import AsyncSession

from core.orchestrator import Orchestrator
from core.task_graph import TaskStatus, create_task


@pytest.mark.asyncio
async def test_scenario_partial_approval(db_session: AsyncSession):
    """
    Scenario: User approves Step 1 but later Step 2 requires manual approval.
    """
    from core.context.manager import ContextManager
    from core.context.rules_parser import RulesParser
    
    rules = RulesParser()
    ctx = ContextManager()
    orch = Orchestrator(db_session, rules, ctx)
    
    graph_id = "partial-approval-graph"
    
    # Pre-populate graph with 2 pending tasks
    task1 = await create_task(db_session, graph_id=graph_id, agent_type="coder", title="T1", description="D1")
    task2 = await create_task(db_session, graph_id=graph_id, agent_type="tester", title="T2", description="D2")
    await db_session.commit()
    
    # Mock Task 1 to complete successfully
    async def mock_exec1(*args, **kwargs):
        yield {"type": "token", "text": "T1 working"}
        yield {"type": "result", "result": "T1 done"}

    # Mock Task 2 to require approval
    async def mock_exec2(*args, **kwargs):
        yield {"type": "tool_call", "tool": "shell", "args": {}}

    with patch("core.agents.coder_agent.CoderAgent.execute", side_effect=mock_exec1), \
         patch("core.agents.tester_agent.TesterAgent.execute", side_effect=mock_exec2), \
         patch("core.orchestrator.hive_mind.remember"), \
         patch("core.infrastructure.manager.InfrastructureManager.resolve_model_params", return_value="7B"):
        
        events = []
        async for event in orch.resume(graph_id, "conv-123"):
            events.append(event)
            
    # Verify Task 1 is DONE
    await db_session.refresh(task1)
    assert task1.status == TaskStatus.DONE
    
    # Verify Task 2 is AWAITING_APPROVAL
    await db_session.refresh(task2)
    assert task2.status == TaskStatus.AWAITING_APPROVAL
    
    # Verify events
    event_types = [e["event"] for e in events]
    assert "approval_required" in event_types
    assert "done" not in event_types # Loop should have returned early

@pytest.mark.asyncio
async def test_scenario_task_failure_stops_graph(db_session: AsyncSession):
    """
    Scenario: Task 1 fails, Task 2 should remain PENDING.
    """
    from core.context.manager import ContextManager
    from core.context.rules_parser import RulesParser
    
    rules = RulesParser()
    ctx = ContextManager()
    orch = Orchestrator(db_session, rules, ctx)
    
    graph_id = "failure-stops-graph"
    
    task1 = await create_task(db_session, graph_id=graph_id, agent_type="coder", title="T1", description="D1")
    task2 = await create_task(db_session, graph_id=graph_id, agent_type="tester", title="T2", description="D2")
    await db_session.commit()
    
    async def mock_fail(*args, **kwargs):
        if False: yield {} # Make it a generator
        raise RuntimeError("Crash!")

    with patch("core.agents.coder_agent.CoderAgent.execute", side_effect=mock_fail), \
         patch("core.agents.tester_agent.TesterAgent.execute"), \
         patch("core.infrastructure.manager.InfrastructureManager.resolve_model_params", return_value="7B"):
        
        events = []
        async for event in orch.resume(graph_id, "conv-123"):
            events.append(event)
            
    # Verify Task 1 is FAILED
    await db_session.refresh(task1)
    assert task1.status == TaskStatus.FAILED
    assert task1.error == "Crash!"
    
    # Verify Task 2 is still PENDING
    await db_session.refresh(task2)
    assert task2.status == TaskStatus.PENDING
    
    # Verify failure event
    assert any(e["event"] == "task_updated" and e["data"]["status"] == TaskStatus.FAILED for e in events)

@pytest.mark.asyncio
async def test_scenario_sequential_dependency_integrity(db_session: AsyncSession):
    """
    Scenario: Ensure tasks are executed in creation order (sequential).
    """
    from core.context.manager import ContextManager
    from core.context.rules_parser import RulesParser
    
    rules = RulesParser()
    ctx = ContextManager()
    orch = Orchestrator(db_session, rules, ctx)
    
    graph_id = "sequential-integrity"
    
    # Create 3 tasks
    task1 = await create_task(db_session, graph_id=graph_id, agent_type="coder", title="T1", description="D1")
    task2 = await create_task(db_session, graph_id=graph_id, agent_type="coder", title="T2", description="D2")
    task3 = await create_task(db_session, graph_id=graph_id, agent_type="coder", title="T3", description="D3")
    await db_session.commit()
    
    execution_order = []
    
    async def mock_exec(node_id):
        async def _exec(*args, **kwargs):
            execution_order.append(node_id)
            yield {"type": "result", "result": "ok"}
        return _exec

    with patch("core.agents.coder_agent.CoderAgent.execute") as mock_coder, \
         patch("core.orchestrator.hive_mind.remember"), \
         patch("core.infrastructure.manager.InfrastructureManager.resolve_model_params", return_value="7B"):
        
        # side_effect needs to handle the multiple calls
        mock_coder.side_effect = [
            (await mock_exec(task1.id))(),
            (await mock_exec(task2.id))(),
            (await mock_exec(task3.id))()
        ]
        
        async for _ in orch.resume(graph_id, "conv-123"):
            pass
            
    assert execution_order == [task1.id, task2.id, task3.id]


def test_websocket_plan_approve_execute():
    """
    E2E Integration Scenario: Connect via WebSocket, submit user message,
    receive plan_ready, approve plan, and receive execution completion event.
    """
    from unittest.mock import AsyncMock, patch

    from fastapi.testclient import TestClient

    from main import app

    # Patch heavy lifespan dependencies
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

        # Mock Orchestrator.run async generator
        async def mock_run_gen(*args, **kwargs):
            yield {"event": "token", "data": "Generating plan..."}
            yield {"event": "plan_ready", "data": {"graph_id": "test-graph-123"}}
        mock_run.side_effect = mock_run_gen

        # Mock Orchestrator.resume async generator
        async def mock_resume_gen(*args, **kwargs):
            yield {"event": "token", "data": "Executing plan..."}
            yield {"event": "done", "data": {"graph_id": "test-graph-123"}}
        mock_resume.side_effect = mock_resume_gen

        def wait_for_event(ws, event_type):
            while True:
                ev = ws.receive_json()
                if ev.get("event") == event_type:
                    return ev

        # Connect using TestClient (it handles FastAPI lifecycle)
        with TestClient(app) as client:
            with client.websocket_connect("/ws/conv-123?token=mocked-token") as websocket:
                # 1. Send user message
                websocket.send_json({"type": "message", "content": "Create a new file"})

                # 2. Receive token event
                ev1 = wait_for_event(websocket, "token")
                assert ev1["data"] == "Generating plan..."

                # 3. Receive plan_ready event
                ev2 = wait_for_event(websocket, "plan_ready")
                assert ev2["data"]["graph_id"] == "test-graph-123"

                # 4. Approve plan
                websocket.send_json({"type": "approve_plan", "graph_id": "test-graph-123"})

                # 5. Receive execution token event
                ev3 = wait_for_event(websocket, "token")
                assert ev3["data"] == "Executing plan..."

                # 6. Receive done event
                ev4 = wait_for_event(websocket, "done")
                assert ev4["data"]["graph_id"] == "test-graph-123"

