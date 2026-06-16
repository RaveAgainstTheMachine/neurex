from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from core.context.neural_linter import NeuralLinter


@pytest.fixture
def linter():
    with patch("core.mcp.tools.filesystem.get_workspace_root", return_value="/tmp/workspace"):
        return NeuralLinter()

@pytest.mark.asyncio
async def test_neural_linter_no_standards(linter):
    with patch("os.path.exists", return_value=False):
        valid, reason = await linter.verify_mutation("test_tool", {"path": "test.py", "content": "test"}, "conv_id")
        assert valid is True
        assert reason == "No standards defined."

@pytest.mark.asyncio
async def test_neural_linter_disabled(linter):
    with patch("os.path.exists", return_value=True):
        with patch.dict("os.environ", {"LINTER_ENABLED": "false"}):
            valid, reason = await linter.verify_mutation("test_tool", {"path": "test.py", "content": "test"}, "conv_id")
            assert valid is True
            assert reason == "Linter disabled."

@pytest.mark.asyncio
async def test_neural_linter_mock_mode(linter):
    with patch("os.path.exists", return_value=True):
        with patch.dict("os.environ", {"LINTER_ENABLED": "true", "NEUREX_MOCK_LLM": "true"}):
            valid, reason = await linter.verify_mutation("test_tool", {"path": "test.py", "content": "test"}, "conv_id")
            assert valid is True
            assert reason == "Mock mode bypass"

@pytest.mark.asyncio
async def test_neural_linter_no_content(linter):
    with patch("os.path.exists", return_value=True):
        with patch.dict("os.environ", {"LINTER_ENABLED": "true", "NEUREX_MOCK_LLM": "false"}):
            valid, reason = await linter.verify_mutation("test_tool", {"path": "test.py"}, "conv_id") # no content
            assert valid is True
            assert reason == ""

@pytest.mark.asyncio
async def test_neural_linter_pass(linter):
    with patch("os.path.exists", return_value=True):
        with patch("builtins.open", MagicMock()):
            with patch.dict("os.environ", {"LINTER_ENABLED": "true", "NEUREX_MOCK_LLM": "false"}):
                with patch("core.infrastructure.mesh.mesh_router.get_best_inference_node", new_callable=AsyncMock, return_value="http://localhost:11434"):
                    with patch("httpx.AsyncClient.post", new_callable=AsyncMock) as mock_post:
                        mock_res = MagicMock()
                        mock_res.status_code = 200
                        mock_res.json.return_value = {"message": {"content": '{"verdict": "PASS"}'}}
                        mock_post.return_value = mock_res
                        
                        valid, reason = await linter.verify_mutation("test_tool", {"path": "test.py", "content": "test"}, "conv_id")
                        assert valid is True

@pytest.mark.asyncio
async def test_neural_linter_fail(linter):
    with patch("os.path.exists", return_value=True):
        with patch("builtins.open", MagicMock()):
            with patch.dict("os.environ", {"LINTER_ENABLED": "true", "NEUREX_MOCK_LLM": "false"}):
                with patch("core.infrastructure.mesh.mesh_router.get_best_inference_node", new_callable=AsyncMock, return_value="http://localhost:11434"):
                    with patch("httpx.AsyncClient.post", new_callable=AsyncMock) as mock_post:
                        mock_res = MagicMock()
                        mock_res.status_code = 200
                        mock_res.json.return_value = {"message": {"content": '{"verdict": "FAIL", "reason": "Bad design"}'}}
                        mock_post.return_value = mock_res
                        
                        valid, reason = await linter.verify_mutation("test_tool", {"path": "test.py", "content": "test"}, "conv_id")
                        assert valid is False
                        assert reason == "Bad design"

@pytest.mark.asyncio
async def test_neural_linter_exception(linter):
    with patch("os.path.exists", return_value=True):
        with patch("builtins.open", MagicMock()):
            with patch.dict("os.environ", {"LINTER_ENABLED": "true", "NEUREX_MOCK_LLM": "false"}):
                with patch("core.infrastructure.mesh.mesh_router.get_best_inference_node", new_callable=AsyncMock, side_effect=Exception("network error")):
                    valid, reason = await linter.verify_mutation("test_tool", {"path": "test.py", "content": "test"}, "conv_id")
                    assert valid is True
                    assert reason == "Linter internal error."
