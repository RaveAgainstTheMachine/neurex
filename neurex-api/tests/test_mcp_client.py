import json
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from core.mcp.client import (
    MCPClient,
    get_tool_permission,
    run_add_global_memory,
    run_genetic_optimization,
    run_hardware_benchmark,
    run_hyperplan,
    run_query_global_memory,
    set_tool_permission,
)


@pytest.mark.asyncio
async def test_run_hyperplan():
    with patch("core.agents.base_agent.BaseAgent"):
        with patch("core.context.manager.ContextManager"):
            with patch("core.harness.hyperplan.HyperPlan.generate_blueprint", new_callable=AsyncMock) as mock_gen:
                mock_gen.return_value = {"status": "ok"}
                res = await run_hyperplan("query")
                assert "ok" in res

@pytest.mark.asyncio
async def test_run_genetic_optimization():
    with patch("core.agents.base_agent.BaseAgent"):
        with patch("core.context.manager.ContextManager"):
            with patch("core.agents.genetic_agent.GeneticAgent.evolve_module", new_callable=AsyncMock) as mock_evolve:
                mock_evolve.return_value = True
                res = await run_genetic_optimization("test.py")
                assert "COMPLETED" in res

@pytest.mark.asyncio
async def test_global_memory():
    with patch("core.context.global_memory.global_memory.add_pointer", new_callable=AsyncMock):
        res = await run_add_global_memory("key", "content")
        assert "added" in res
        
    with patch("core.context.global_memory.global_memory.query_memory", new_callable=AsyncMock) as mock_q:
        mock_q.return_value = "mem"
        assert await run_query_global_memory("test") == "mem"

@pytest.mark.asyncio
async def test_run_hardware_benchmark():
    with patch("core.infrastructure.benchmarker.hardware_benchmarker.run_benchmark", new_callable=AsyncMock) as mock_run:
        mock_run.return_value = {"cpu": "ok"}
        res = await run_hardware_benchmark()
        assert "ok" in res

@pytest.mark.asyncio
async def test_get_set_tool_permission():
    with patch("core.task_graph.async_session") as mock_session_maker:
        mock_ctx = AsyncMock()
        mock_session_maker.return_value = mock_ctx
        mock_session = AsyncMock()
        mock_ctx.__aenter__.return_value = mock_session
        
        # Test Set
        mock_perm = MagicMock()
        mock_session.get.return_value = mock_perm
        
        await set_tool_permission("test_tool", "allow")
        assert mock_perm.rule == "allow"
        mock_session.commit.assert_called_once()
        
        # Test Get
        mock_result = MagicMock()
        mock_result.first.return_value = mock_perm
        mock_session.exec.return_value = mock_result
        res = await get_tool_permission("test_tool")
        assert res == "allow"

@pytest.mark.asyncio
async def test_mcp_client_call():
    client = MCPClient()
    
    with patch("core.mcp.client.get_tool_permission", return_value="allow"):
        with patch("core.security.governance.governance_manager.is_authorized", return_value=True):
            
            # Tool exists
            async def mock_tool(*args, **kwargs):
                return "tool_success"
                
            with patch.dict("core.mcp.client.TOOL_REGISTRY", {"test_tool": mock_tool}):
                res_str = await client.call("test_tool", {"arg": "1"})
                res = json.loads(res_str)
                assert res["success"] is True
                assert res["result"] == "tool_success"
                
            # Error in tool
            async def mock_error_tool(*args, **kwargs):
                raise Exception("failed")
            
            with patch.dict("core.mcp.client.TOOL_REGISTRY", {"test_error": mock_error_tool}):
                res_str = await client.call("test_error", {})
                res = json.loads(res_str)
                assert res["success"] is False
                assert "failed" in res["error"]
                
            # Tool missing, check skill
            with patch.object(client.skills, "get_skill_for_tool", return_value="skill1"):
                with patch.object(client.skills, "execute_skill_tool", new_callable=AsyncMock) as mock_exec:
                    mock_exec.return_value = "skill_success"
                    res_str = await client.call("missing_tool", {})
                    res = json.loads(res_str)
                    assert res["success"] is True
                    assert res["result"] == "skill_success"
