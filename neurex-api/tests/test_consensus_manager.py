from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from core.collaboration.consensus import ConsensusManager


@pytest.fixture
def manager():
    return ConsensusManager()

def test_is_protected(manager):
    with patch("core.settings.manager.settings_manager.get", return_value=True):
        assert manager.is_protected("core/agents/test.py") is True
        assert manager.is_protected("random/path.py") is False
        
    with patch("core.settings.manager.settings_manager.get", return_value=False):
        assert manager.is_protected("core/agents/test.py") is False

@pytest.mark.asyncio
async def test_submit_and_cast_vote(manager):
    res = await manager.submit_proposal("test.py", "content", "requester1")
    assert "CONSENSUS_REQUIRED" in res
    assert "test.py" in manager.proposals
    assert manager.proposals["test.py"].votes["requester1"] is True
    
    # Cast more votes to reach consensus
    res_v1 = await manager.cast_vote("test.py", "voter1", True)
    assert res_v1 is False # 2 votes total
    
    res_v2 = await manager.cast_vote("test.py", "voter2", True)
    assert res_v2 is True # 3 votes total
    
    # Test unknown path
    assert await manager.cast_vote("unknown.py", "v", True) is False

@pytest.mark.asyncio
async def test_evaluate_mutation(manager):
    reviewers = [MagicMock(agent_type="a1", model="m1"), MagicMock(agent_type="a2", model="m2")]
    
    with patch.object(manager, "_prompt_agent_for_vote", AsyncMock(return_value=True)):
        res = await manager.evaluate_mutation({"path": "test.py", "content": "c", "requester": "r"}, reviewers, "conv1")
        assert res is True
        
    manager.clear_proposal("test.py")
    assert "test.py" not in manager.proposals
    
@pytest.mark.asyncio
async def test_evaluate_mutation_invalid(manager):
    res = await manager.evaluate_mutation({}, [], "conv1")
    assert res is False

@pytest.mark.asyncio
async def test_prompt_agent_for_vote(manager):
    agent = MagicMock(agent_type="a1")
    
    class MockResponse:
        status_code = 200
        def json(self):
            return {"message": {"content": '{"verdict": "REJECT", "reason": "bad"}'}}
            
    mock_client_instance = AsyncMock()
    mock_client_instance.post.return_value = MockResponse()
    
    mock_client = MagicMock()
    mock_client.__aenter__.return_value = mock_client_instance
    
    with patch("core.infrastructure.mesh.mesh_router.get_best_inference_node", AsyncMock(return_value="http://mock")):
        with patch("httpx.AsyncClient", return_value=mock_client):
            res = await manager._prompt_agent_for_vote(agent, "test.py", "content")
            assert res is False # verdict was REJECT

@pytest.mark.asyncio
async def test_prompt_agent_fallback(manager):
    agent = MagicMock(agent_type="a1")
    
    # Simulate network error
    with patch("core.infrastructure.mesh.mesh_router.get_best_inference_node", AsyncMock(side_effect=Exception("error"))):
        res = await manager._prompt_agent_for_vote(agent, "test.py", "content")
        # Should fallback to True
        assert res is True
