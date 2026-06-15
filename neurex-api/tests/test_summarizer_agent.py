from unittest.mock import MagicMock

import pytest

from core.agents.summarizer_agent import SummarizerAgent


@pytest.mark.asyncio
async def test_summarize_empty(mock_ollama_stream):
    # Mock RulesParser and ContextManager
    rules = MagicMock()
    ctx = MagicMock()
    agent = SummarizerAgent(rules, ctx)
    # empty
    result = await agent.summarize([])
    assert result == ""

@pytest.mark.asyncio
async def test_summarize_messages(mock_ollama_stream):
    rules = MagicMock()
    ctx = MagicMock()
    agent = SummarizerAgent(rules, ctx)
    
    # Mock the stream method properly
    async def fake_stream(msgs):
        yield {"type": "token", "text": "This "}
        yield {"type": "token", "text": "is summary."}
        yield {"type": "done"}
        
    agent.stream = fake_stream
    
    msgs = [
        {"role": "user", "content": "Make a file"},
        {"role": "assistant", "tool_calls": [{"function": {"name": "write_to_file"}}]},
    ]
    result = await agent.summarize(msgs)
    assert result == "This is summary."

@pytest.mark.asyncio
async def test_execute():
    rules = MagicMock()
    ctx = MagicMock()
    agent = SummarizerAgent(rules, ctx)
    
    async def fake_stream(msgs):
        yield {"type": "token", "text": "Summary result"}
        yield {"type": "done"}
    agent.stream = fake_stream
    
    gen = agent.execute({"description": "Test desc"}, "conv-1")
    res = [x async for x in gen]
    assert len(res) == 1
    assert res[0] == {"type": "result", "result": "Summary result"}

def test_compress_history():
    rules = MagicMock()
    ctx = MagicMock()
    agent = SummarizerAgent(rules, ctx)
    
    msgs = [
        {"role": "system", "content": "Sys"},
        {"role": "user", "content": "1"},
        {"role": "assistant", "content": "2"},
        {"role": "user", "content": "3"},
        {"role": "assistant", "content": "4"},
        {"role": "user", "content": "5"},
        {"role": "assistant", "content": "6"},
    ]
    
    to_summarize, to_keep = agent.compress_history(msgs, keep_last=2)
    assert len(to_summarize) == 4  # 1, 2, 3, 4
    assert len(to_keep) == 3       # Sys, 5, 6
    assert to_keep[0]["role"] == "system"
    assert to_keep[-1]["content"] == "6"

def test_compress_history_no_need():
    rules = MagicMock()
    ctx = MagicMock()
    agent = SummarizerAgent(rules, ctx)
    
    msgs = [
        {"role": "system", "content": "Sys"},
        {"role": "user", "content": "1"},
    ]
    
    to_summarize, to_keep = agent.compress_history(msgs, keep_last=2)
    assert len(to_summarize) == 0
    assert len(to_keep) == 2
