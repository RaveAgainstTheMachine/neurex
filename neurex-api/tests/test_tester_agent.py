from unittest.mock import AsyncMock, MagicMock

import pytest

from core.agents.tester_agent import TesterAgent
from core.task_graph import TaskStatus


@pytest.fixture
def agent():
    return TesterAgent(rules=[], ctx=MagicMock())

@pytest.mark.asyncio
async def test_tester_execution_no_tools(agent):
    agent.build_system_prompt = AsyncMock(return_value="sys")
    
    async def mock_stream(*args, **kwargs):
        yield {"type": "token", "text": "tests passed"}
        yield {"type": "done", "full_text": "tests passed"}
        
    agent.stream = mock_stream
    
    events = []
    async for e in agent.execute({"title": "T", "description": "D", "context": "code"}, "conv1"):
        events.append(e)
        
    assert events[0] == {"type": "status", "status": TaskStatus.TESTING}
    assert events[-1] == {"type": "result", "result": "tests passed"}

@pytest.mark.asyncio
async def test_tester_infra_failure(agent):
    agent.build_system_prompt = AsyncMock(return_value="sys")
    agent.dispatch_tool = AsyncMock(return_value="Docker not found on host")
    
    async def mock_stream(*args, **kwargs):
        call_dict = {"id": "1", "function": {"name": "run_command", "arguments": "{}"}}
        yield {"type": "tool_call", "call": call_dict}
        yield {"type": "done", "full_text": ""}
        
    agent.stream = mock_stream
    
    events = []
    async for e in agent.execute({"description": "D"}, "conv1"):
        events.append(e)
        
    assert "TEST INFRASTRUCTURE UNAVAILABLE" in events[-1]["result"]
    assert agent.dispatch_tool.call_count == 1

@pytest.mark.asyncio
async def test_tester_max_rounds(agent):
    agent.build_system_prompt = AsyncMock(return_value="sys")
    agent.dispatch_tool = AsyncMock(return_value="tool output")
    
    async def mock_stream(*args, **kwargs):
        call_dict = {"id": "1", "function": {"name": "read_file", "arguments": "{}"}}
        yield {"type": "tool_call", "call": call_dict}
        yield {"type": "done", "full_text": ""}
        
    agent.stream = mock_stream
    
    events = []
    async for e in agent.execute({"description": "D"}, "conv1"):
        events.append(e)
        
    assert agent.dispatch_tool.call_count == 5
    assert events[-1]["result"] == "Max rounds reached."
