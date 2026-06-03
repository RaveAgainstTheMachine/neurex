"""
tests/test_hello_world_e2e.py
End-to-End E2E test for the true hello world agentic pipeline.
Validates the dynamic workspace binding, single-step plan auto-approval,
and safe-write HITL bypass.
"""

from __future__ import annotations

import os
import shutil
import tempfile
from pathlib import Path

import pytest

from core.context.manager import ContextManager
from core.context.rules_parser import RulesParser
from core.orchestrator import Orchestrator
from core.task_graph import get_graph


@pytest.fixture
def temp_workspace():
    """Create a temporary workspace directory."""
    temp_dir = tempfile.mkdtemp(prefix="neurex-e2e-ws-")
    yield Path(temp_dir)
    shutil.rmtree(temp_dir, ignore_errors=True)


@pytest.mark.asyncio
async def test_hello_world_e2e_flow(db_session, temp_workspace):
    """
    Validates that sending 'Create hello.py' to a dynamic workspace:
    1. Bypasses the plan approval step (single-step auto-approval).
    2. Bypasses the HITL tool approval step (safe write auto-approval).
    3. Physically creates the file in the dynamic workspace.
    """
    # 1. Bind to dynamic workspace
    os.environ["NEUREX_MOCK_LLM"] = "true"
    os.environ["WORKSPACE_PATH"] = str(temp_workspace)
    os.environ["AUTONOMY_CEILING"] = "limited"

    # Pre-verify file does not exist
    hello_file = temp_workspace / "hello.py"
    assert not hello_file.exists()

    # 2. Instantiate real Orchestrator components
    rules = RulesParser()
    ctx = ContextManager()
    orch = Orchestrator(db_session, rules, ctx)

    # 3. Send "Create hello.py"
    events = []
    async for event in orch.run("Create hello.py", "e2e-test-hello-world-conv"):
        events.append(event)

    # 4. Assert plan_ready was auto-approved and yielded execution events immediately
    plan_ready_event = next((e for e in events if e["event"] == "plan_ready"), None)
    assert plan_ready_event is not None
    assert plan_ready_event["data"]["auto_approved"] is True

    # 5. Assert it completed without a tool approval event
    approval_event = next((e for e in events if e["event"] == "approval_required"), None)
    assert approval_event is None, f"Expected no approval required (safe write bypass). Found: {approval_event}"

    done_event = next((e for e in events if e["event"] == "done"), None)
    assert done_event is not None, f"Expected complete execution. Events: {events}"

    # 6. Verify SQLite database persistence updates
    graph_id = plan_ready_event["data"]["graph_id"]
    db_session.expire_all()
    tasks = await get_graph(db_session, graph_id)
    coder_node = next(t for t in tasks if t.agent_type == "coder")
    assert coder_node.status.value.upper() == "DONE"

    # 7. Physical side-effect verification
    assert hello_file.exists(), "File hello.py should have been physically created in the temp workspace."
    file_content = hello_file.read_text()
    assert "# Hello from Mock" in file_content or "hello.py" in file_content
