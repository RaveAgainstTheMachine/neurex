from unittest.mock import MagicMock, patch

import pytest

from core.mcp.servers.neural_harness import run_neural_harness


@pytest.mark.asyncio
async def test_run_neural_harness():
    async def mock_harness_run(query, conversation_id):
        yield {"type": "step", "content": "running"}
        yield {"type": "result", "result": "mocked harness response"}

    mock_harness_instance = MagicMock()
    mock_harness_instance.run = mock_harness_run

    with patch("core.harness.engine.NeuralHarness", return_value=mock_harness_instance):
        with patch("core.agents.base_agent.BaseAgent") as mock_agent_class:
            mock_agent = MagicMock()
            mock_agent_class.return_value = mock_agent

            res = await run_neural_harness("do something", "some-model")
            assert res == "mocked harness response"
            mock_agent_class.assert_called_once()
