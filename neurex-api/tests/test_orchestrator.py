"""
tests/test_orchestrator.py
Tests for the Supervisor Orchestrator: planning, decomposition, and execution loop.
"""

from __future__ import annotations

from unittest.mock import AsyncMock, patch

import pytest
from sqlmodel.ext.asyncio.session import AsyncSession

from core.orchestrator import Orchestrator
from core.task_graph import TaskStatus


@pytest.mark.asyncio
async def test_orchestrator_run_creates_plan(db_session: AsyncSession):
    """Orchestrator.run should create a planner node and sub-tasks."""
    from core.context.manager import ContextManager
    from core.context.rules_parser import RulesParser

    rules = RulesParser()
    ctx = ContextManager()
    orch = Orchestrator(db_session, rules, ctx)

    # Mock PlannerAgent.plan to return a 2-step plan
    mock_plan = [
        {"title": "Step 1", "description": "Do X", "agent": "coder"},
        {"title": "Step 2", "description": "Do Y", "agent": "tester"},
    ]

    async def mock_plan_stream(*args, **kwargs):
        yield {"type": "token", "text": "Planning... "}
        yield {"type": "result", "plan": mock_plan}

    with (
        patch("core.agents.planner_agent.PlannerAgent.plan", side_effect=mock_plan_stream),
        patch("core.orchestrator.hive_mind.recall", return_value=[]),
        patch("core.orchestrator.Orchestrator._create_git_snapshot", new_callable=AsyncMock),
        patch(
            "core.infrastructure.manager.InfrastructureManager.resolve_model_params",
            new_callable=AsyncMock,
            return_value="7B",
        ),
    ):
        events = []
        async for event in orch.run("Build a web app", "conv-123"):
            events.append(event)

    # Verify events
    event_types = [e["event"] for e in events]
    assert "task_created" in event_types
    assert "task_updated" in event_types
    assert "plan_ready" in event_types

    # Verify DB state
    graph_id = events[0]["data"]["graph_id"]
    from core.task_graph import get_graph

    tasks = await get_graph(db_session, graph_id)

    # Should have 3 tasks: 1 planner (parent) + 2 sub-tasks
    assert len(tasks) == 3

    planner_node = next(t for t in tasks if t.agent_type == "planner")
    sub_tasks = [t for t in tasks if t.parent_id == planner_node.id]
    assert len(sub_tasks) == 2
    assert {t.agent_type for t in sub_tasks} == {"coder", "tester"}
    assert planner_node.status == TaskStatus.AWAITING_APPROVAL


@pytest.mark.asyncio
async def test_orchestrator_resume_executes_tasks(db_session: AsyncSession):
    """Orchestrator.resume should execute PENDING tasks in order."""
    from core.context.manager import ContextManager
    from core.context.rules_parser import RulesParser

    rules = RulesParser()
    ctx = ContextManager()
    orch = Orchestrator(db_session, rules, ctx)

    graph_id = "test-graph-resume"
    # Create a pending task
    from core.task_graph import create_task

    task = await create_task(
        db_session, graph_id=graph_id, agent_type="coder", title="Write Code", description="impl"
    )
    await db_session.commit()

    async def mock_execute_stream(*args, **kwargs):
        yield {"type": "token", "text": "Coding... "}
        yield {"type": "result", "result": "Done!"}

    with (
        patch("core.agents.coder_agent.CoderAgent.execute", side_effect=mock_execute_stream),
        patch("core.orchestrator.hive_mind.remember"),
        patch(
            "core.infrastructure.manager.InfrastructureManager.resolve_model_params",
            new_callable=AsyncMock,
            return_value="7B",
        ),
    ):
        events = []
        async for event in orch.resume(graph_id, "conv-123"):
            events.append(event)

    # Verify events
    event_types = [e["event"] for e in events]
    assert "task_updated" in event_types  # THINKING
    assert "task_updated" in event_types  # DONE
    assert "done" in event_types

    # Verify DB state
    await db_session.refresh(task)
    assert task.status == TaskStatus.DONE
    assert task.result == "Done!"


@pytest.mark.asyncio
async def test_orchestrator_hitl_approval_required(db_session: AsyncSession):
    """Orchestrator should pause and yield approval_required for restricted tools."""
    from core.context.manager import ContextManager
    from core.context.rules_parser import RulesParser

    rules = RulesParser()
    ctx = ContextManager()
    orch = Orchestrator(db_session, rules, ctx)
    orch.set_autonomy_level("limited")

    graph_id = "test-graph-hitl"
    from core.task_graph import create_task

    task = await create_task(
        db_session, graph_id=graph_id, agent_type="coder", title="Write", description="impl"
    )
    await db_session.commit()

    async def mock_execute_hitl(*args, **kwargs):
        yield {"type": "status", "status": "thinking"}
        yield {"type": "tool_call", "tool": "filesystem", "args": {"path": "test.py"}}

    with (
        patch("core.agents.coder_agent.CoderAgent.execute", side_effect=mock_execute_hitl),
        patch(
            "core.infrastructure.manager.InfrastructureManager.resolve_model_params",
            new_callable=AsyncMock,
            return_value="7B",
        ),
    ):
        events = []
        async for event in orch.resume(graph_id, "conv-123"):
            events.append(event)

    # Verify HITL event
    event_types = [e["event"] for e in events]
    assert "approval_required" in event_types

    # Verify task status is AWAITING_APPROVAL
    await db_session.refresh(task)
    assert task.status == TaskStatus.AWAITING_APPROVAL


@pytest.mark.asyncio
async def test_orchestrator_execute_inline_edit_mock_env(db_session: AsyncSession, tmp_path):
    """Orchestrator.execute_inline_edit should run fallback in Mock LLM environment."""
    import os

    from core.context.manager import ContextManager
    from core.context.rules_parser import RulesParser

    rules = RulesParser()
    ctx = ContextManager()
    orch = Orchestrator(db_session, rules, ctx)
    orch.workspace = tmp_path

    # Create dummy file
    dummy_file = tmp_path / "hello.py"
    dummy_file.write_text("print('hello')")

    with patch.dict(os.environ, {"NEUREX_MOCK_LLM": "true"}):
        events = []
        async for event in orch.execute_inline_edit(
            "hello.py",
            prompt="add a comment",
            selection="print('hello')",
            range_coords=None,
            task_id="task-inline-mock",
            conversation_id="conv-123",
        ):
            events.append(event)

    event_types = [e["event"] for e in events]
    assert "task_updated" in event_types
    assert "inline_edit_diff" in event_types

    diff_event = next(e for e in events if e["event"] == "inline_edit_diff")
    assert diff_event["data"]["path"] == "hello.py"
    assert diff_event["data"]["original"] == "print('hello')"
    assert "# Refactored by Mock AI: add a comment" in diff_event["data"]["modified"]


@pytest.mark.asyncio
async def test_orchestrator_execute_inline_edit_stream(db_session: AsyncSession, tmp_path):
    """Orchestrator.execute_inline_edit should stream custom LLM tokens in live mode."""
    import os

    from core.context.manager import ContextManager
    from core.context.rules_parser import RulesParser

    rules = RulesParser()
    ctx = ContextManager()
    orch = Orchestrator(db_session, rules, ctx)
    orch.workspace = tmp_path

    # Create dummy file
    dummy_file = tmp_path / "hello.py"
    dummy_file.write_text("print('hello')")

    async def mock_agent_stream(*args, **kwargs):
        yield {"type": "token", "text": "```python\nprint('hello')\n# inline comments\n```"}
        yield {"type": "done", "full_text": "```python\nprint('hello')\n# inline comments\n```"}

    with (
        patch.dict(os.environ, {"NEUREX_MOCK_LLM": "false"}),
        patch("core.agents.base_agent.BaseAgent.stream", side_effect=mock_agent_stream),
        patch("core.orchestrator.Orchestrator._create_git_snapshot", new_callable=AsyncMock),
        patch(
            "core.infrastructure.manager.InfrastructureManager.resolve_model_params",
            new_callable=AsyncMock,
            return_value="7B",
        ),
    ):
        events = []
        async for event in orch.execute_inline_edit(
            "hello.py",
            prompt="add inline comments",
            selection="print('hello')",
            range_coords=None,
            task_id="task-inline-stream",
            conversation_id="conv-123",
        ):
            events.append(event)

    event_types = [e["event"] for e in events]
    assert "task_updated" in event_types
    assert "inline_edit_diff" in event_types

    diff_event = next(e for e in events if e["event"] == "inline_edit_diff")
    # Verified stripped markdown blocks
    assert diff_event["data"]["modified"] == "print('hello')\n# inline comments"
