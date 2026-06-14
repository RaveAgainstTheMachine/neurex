from unittest.mock import AsyncMock, MagicMock

import pytest

from core.harness.hyperplan import HyperPlan


@pytest.fixture
def mock_agent():
    agent = MagicMock()
    agent.model = "test-model"
    agent.ctx = MagicMock()
    agent.ctx.explorer = AsyncMock()
    agent.ctx.explorer.hybrid_search.return_value = [{"document": "test doc"}]
    
    async def mock_stream(*args, **kwargs):
        yield {"type": "token", "text": "chunk1"}
        yield {"type": "token", "text": "chunk2"}
        
    agent.stream = mock_stream
    return agent

@pytest.mark.asyncio
async def test_hyperplan_generate_blueprint(mock_agent):
    hp = HyperPlan(mock_agent)
    
    # Mock ask_brain to return specific JSON in synthesis pass
    # It gets called 4 times.
    call_count = 0
    async def mock_ask_brain(prompt, model):
        nonlocal call_count
        call_count += 1
        if call_count == 4:
            return '{"tasks": [{"agent": "coder", "title": "t", "description": "d"}]}'
        return f"result pass {call_count}"
        
    hp._ask_brain = mock_ask_brain
    
    res = await hp.generate_blueprint("test task")
    assert "tasks" in res
    assert res["tasks"][0]["agent"] == "coder"
    assert call_count == 4
    
@pytest.mark.asyncio
async def test_hyperplan_ask_brain(mock_agent):
    hp = HyperPlan(mock_agent)
    
    res = await hp._ask_brain("prompt", "model")
    assert res == "chunk1chunk2"

@pytest.mark.asyncio
async def test_hyperplan_synthesis_fallback(mock_agent):
    hp = HyperPlan(mock_agent)
    
    # Test invalid json fallback
    async def mock_ask_brain(*args, **kwargs):
        return "invalid json output"
        
    hp._ask_brain = mock_ask_brain
    
    res = await hp._pass_synthesis("opt")
    assert "raw_blueprint" in res
    assert res["raw_blueprint"] == "invalid json output"
