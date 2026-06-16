from unittest.mock import AsyncMock, MagicMock

import pytest

from core.agents.researcher_agent import ResearcherAgent
from core.task_graph import TaskStatus


@pytest.fixture
def agent():
    return ResearcherAgent(rules=[], ctx=MagicMock())

@pytest.mark.asyncio
async def test_researcher_execution_no_tools(agent):
    agent.rag_context = AsyncMock(return_value="rag")
    agent.build_system_prompt = AsyncMock(return_value="sys")
    
    # Mock stream to just return a text chunk and done
    async def mock_stream(*args, **kwargs):
        yield {"type": "token", "text": "research result"}
        yield {"type": "done", "full_text": "research result"}
    
    agent.stream = mock_stream
    
    events = []
    async for e in agent.execute({"title": "T", "description": "D"}, "conv1"):
        events.append(e)
        
    assert events[0] == {"type": "status", "status": TaskStatus.THINKING}
    assert {"type": "token", "text": "research result"} in events
    assert events[-1] == {"type": "result", "result": "research result"}

@pytest.mark.asyncio
async def test_researcher_execution_with_tools(agent):
    agent.rag_context = AsyncMock(return_value="rag")
    agent.build_system_prompt = AsyncMock(return_value="sys")
    agent.dispatch_tool = AsyncMock(return_value="tool output")
    
    # Mock stream to return a tool call on first round, and text on second
    call_idx = 0
    async def mock_stream(messages, *args, **kwargs):
        nonlocal call_idx
        if call_idx == 0:
            call_idx += 1
            call_dict = {"id": "1", "function": {"name": "web_search", "arguments": "{}"}}
            yield {"type": "tool_call", "call": call_dict}
            yield {"type": "done", "full_text": ""}
        else:
            yield {"type": "token", "text": "done research"}
            yield {"type": "done", "full_text": "done research"}
            
    agent.stream = mock_stream
    
    events = []
    async for e in agent.execute({"description": "D", "history": [{"role": "user", "content": "hello"}]}, "conv1"):
        events.append(e)
        
    assert agent.dispatch_tool.call_count == 1
    assert events[-1] == {"type": "result", "result": "done research"}

@pytest.mark.asyncio
async def test_researcher_max_rounds(agent):
    agent.rag_context = AsyncMock(return_value="rag")
    agent.build_system_prompt = AsyncMock(return_value="sys")
    agent.dispatch_tool = AsyncMock(return_value="tool output")
    
    # Always return a tool call
    async def mock_stream(*args, **kwargs):
        call_dict = {"id": "1", "function": {"name": "web_search", "arguments": "{}"}}
        yield {"type": "tool_call", "call": call_dict}
        yield {"type": "done", "full_text": ""}
        
    agent.stream = mock_stream
    
    events = []
    async for e in agent.execute({"description": "D"}, "conv1"):
        events.append(e)
        
    assert agent.dispatch_tool.call_count == 5 # max_rounds
    assert events[-1]["result"] == "Researcher reached maximum tool rounds."
