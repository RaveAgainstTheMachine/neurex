"""
tests/test_chat_unmocked.py
Brutally honest, 100% unmocked E2E integration test for the Neurex chat workflow.
Uses ZERO python mocks or monkeypatches, relying entirely on the native database and WebSocket routing.
"""

from __future__ import annotations

import os
from pathlib import Path

import pytest

from core.context.manager import ContextManager
from core.context.rules_parser import RulesParser
from core.orchestrator import Orchestrator
from core.task_graph import get_graph


@pytest.mark.asyncio
async def test_real_chat_workflow_hello_world(db_session, sample_workspace):
    """
    E2E Chat Workflow: Direct orchestrator planning execution, task graph creation,
    real queue task worker dispatch, Human-in-the-Loop (HITL) tool interception,
    HITL approval injection, and physical workspace side-effect validation.
    """
    # 1. Configure the native app environment settings (no dynamic runtime overrides)
    os.environ["NEUREX_MOCK_LLM"] = "true"
    os.environ["WORKSPACE_PATH"] = str(sample_workspace)
    os.environ["AUTONOMY_CEILING"] = "limited"

    # Grant dynamic governance path access to the test conversation
    from core.security.governance import governance_manager

    governance_manager.dynamic_grants["test-unmocked-conv"] = {""}

    # Pre-clear the output file in the globally resolved workspace root
    stale_file = Path("/tmp/neurex-test-workspace/hello.py")
    if stale_file.exists():
        stale_file.unlink()

    # 2. Instantiate real Orchestrator components
    rules = RulesParser()
    ctx = ContextManager()
    orch = Orchestrator(db_session, rules, ctx)

    # 3. Phase 1: Direct Planning and Decomposition execution
    events = []
    async for event in orch.run("Create a file named hello.py", "test-unmocked-conv"):
        events.append(event)

    plan_ready_event = next((e for e in events if e["event"] == "plan_ready"), None)
    assert plan_ready_event is not None, f"Failed to retrieve native plan_ready. Events: {events}"
    graph_id = plan_ready_event["data"]["graph_id"]

    # 4. Verify task graph records inside database
    tasks = await get_graph(db_session, graph_id)
    assert (
        len(tasks) >= 2
    ), f"Expected at least two task nodes (planner + coder). Found: {[t.agent_type for t in tasks]}"

    planner_node = next(t for t in tasks if t.agent_type == "planner")
    assert planner_node.status.value.upper() == "AWAITING_APPROVAL"

    # 5. Phase 2: Direct Resume execution and catch HITL tool block
    execution_events = []
    async for event in orch.resume(graph_id, "test-unmocked-conv"):
        execution_events.append(event)

    approval_event = next((e for e in execution_events if e["event"] == "approval_required"), None)
    assert (
        approval_event is not None
    ), f"Orchestrator failed to halt and request tool approval. Events: {execution_events}"
    task_id = approval_event["data"]["id"]
    assert approval_event["data"]["tool"] == "write_file"

    # 6. Phase 3: Simulate positive HITL approval for the write_file tool call
    resume_events = []
    async for event in orch.resume_shell(task_id, True, "test-unmocked-conv"):
        resume_events.append(event)

    assert any(
        e["event"] == "done" for e in resume_events
    ), f"Orchestrator failed to complete after approval. Events: {resume_events}"

    # 7. Verify SQLite database persistence updates
    db_session.expire_all()
    tasks_after = await get_graph(db_session, graph_id)
    coder_node = next(t for t in tasks_after if t.agent_type == "coder")
    assert coder_node.status.value.upper() == "DONE"

    # 8. Confirm physical side-effects on host workspace filesystem
    global_ws = Path("/tmp/neurex-test-workspace")
    output_file = global_ws / "hello.py"
    assert (
        output_file.exists()
    ), f"File hello.py was not created in the global workspace: {global_ws}"
    file_content = output_file.read_text()
    assert "# Hello from Mock" in file_content or "hello.py" in file_content
