from unittest.mock import AsyncMock, MagicMock

import pytest

from core.agents.commander_agent import CommanderAgent
from core.agents.dependency_agent import DependencyAgent
from core.agents.reviewer_agent import ReviewerAgent
from core.task_graph import TaskStatus


@pytest.fixture
def rules():
    return MagicMock()

@pytest.fixture
def ctx():
    return MagicMock()

@pytest.mark.asyncio
async def test_commander_agent(rules, ctx):
    agent = CommanderAgent(rules=rules, ctx=ctx)
    agent.mcp = MagicMock()
    agent.mcp.call = AsyncMock(return_value="mock intel")
    agent.build_system_prompt = AsyncMock(return_value="sys prompt")
    agent.record_decision = AsyncMock()

    # Success JSON scenario
    async def mock_stream_success(*args, **kwargs):
        yield {"type": "token", "text": '[{"agent_type": "coder", "title": "fix", "description": "do it"}]'}
        yield {"type": "done", "full_text": ""}

    agent.stream = mock_stream_success

    task = {"id": "t1", "progress_summary": "p", "current_error": "e"}
    events = []
    async for e in agent.execute(task, "conv1"):
        events.append(e)

    assert any("REWRITTEN_PLAN" in e.get("result", "") for e in events if e.get("type") == "result")
    assert agent.record_decision.call_count == 1

    # Malformed JSON scenario
    async def mock_stream_malformed(*args, **kwargs):
        yield {"type": "token", "text": 'invalid plan'}
        yield {"type": "done", "full_text": ""}

    agent.stream = mock_stream_malformed
    events = []
    async for e in agent.execute(task, "conv1"):
        events.append(e)
    assert any(e.get("result") == "invalid plan" for e in events if e.get("type") == "result")

@pytest.mark.asyncio
async def test_reviewer_agent(rules, ctx):
    agent = ReviewerAgent(rules=rules, ctx=ctx)
    agent.rag_context = AsyncMock(return_value="mock rag")
    agent.build_system_prompt = AsyncMock(return_value="sys prompt")

    async def mock_stream(*args, **kwargs):
        yield {"type": "token", "text": "APPROVE"}
        yield {"type": "done", "full_text": ""}

    agent.stream = mock_stream

    # Test execution with history list and string
    task_with_list_history = {"description": "desc", "history": [{"role": "user", "content": "u1"}]}
    events = []
    async for e in agent.execute(task_with_list_history, "conv1"):
        events.append(e)
    assert events[0] == {"type": "status", "status": TaskStatus.TESTING}
    assert events[-1] == {"type": "result", "result": "APPROVE"}

    task_with_str_history = {"description": "desc", "history": "history string"}
    events = []
    async for e in agent.execute(task_with_str_history, "conv1"):
        events.append(e)
    assert events[-1] == {"type": "result", "result": "APPROVE"}

@pytest.mark.asyncio
async def test_dependency_agent(rules, ctx):
    agent = DependencyAgent(rules=rules, ctx=ctx)
    agent.build_system_prompt = AsyncMock(return_value="sys prompt")
    agent.dispatch_tool = AsyncMock(return_value="tool output")

    async def mock_stream(*args, **kwargs):
        yield {"type": "token", "text": "auditing"}
        yield {"type": "tool_call", "call": {"id": "c1", "function": {"name": "run_command"}}}
        yield {"type": "done", "full_text": ""}

    agent.stream = mock_stream

    task = {"title": "t", "description": "d", "history": "h"}
    events = []
    async for e in agent.execute(task, "conv1"):
        events.append(e)

    assert any(e.get("type") == "tool_call" for e in events)
    assert any(e.get("type") == "result" for e in events)
    assert agent.dispatch_tool.call_count == 1
