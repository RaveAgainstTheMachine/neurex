from unittest.mock import AsyncMock, MagicMock, patch

import httpx
import pytest

from core.mcp.ollama import ollama_manager


@pytest.fixture
def mock_client():
    client = AsyncMock(spec=httpx.AsyncClient)
    ollama_manager.client = client
    return client

@pytest.mark.asyncio
async def test_get_running_models(mock_client):
    mock_resp = MagicMock()
    mock_resp.json.return_value = {"models": [{"name": "qwen2.5-coder:7b"}]}
    mock_resp.raise_for_status = MagicMock()
    mock_client.get.return_value = mock_resp

    models = await ollama_manager.get_running_models()
    assert len(models) == 1
    assert models[0]["name"] == "qwen2.5-coder:7b"

@pytest.mark.asyncio
async def test_get_running_models_unreachable(mock_client):
    mock_client.get.side_effect = httpx.ConnectError("Unreachable")
    models = await ollama_manager.get_running_models()
    assert models == []

@pytest.mark.asyncio
async def test_get_tags(mock_client):
    mock_resp = MagicMock()
    mock_resp.json.return_value = {"models": [{"name": "llama3:8b"}]}
    mock_resp.raise_for_status = MagicMock()
    mock_client.get.return_value = mock_resp

    tags = await ollama_manager.get_tags()
    assert len(tags) == 1
    assert tags[0]["name"] == "llama3:8b"

@pytest.mark.asyncio
async def test_generate_sync(mock_client):
    mock_resp = MagicMock()
    mock_resp.json.return_value = {"response": "Hello"}
    mock_resp.raise_for_status = MagicMock()
    mock_client.post.return_value = mock_resp

    result = await ollama_manager.generate("test-model", "test prompt")
    assert result["response"] == "Hello"
    mock_client.post.assert_called_once()

@pytest.mark.asyncio
async def test_chat_sync(mock_client):
    mock_resp = MagicMock()
    mock_resp.json.return_value = {"message": {"content": "Hi"}}
    mock_resp.raise_for_status = MagicMock()
    mock_client.post.return_value = mock_resp

    result = await ollama_manager.chat("test-model", [{"role": "user", "content": "Hi"}])
    assert result["message"]["content"] == "Hi"

@pytest.mark.asyncio
async def test_ensure_model_pulls_if_missing(mock_client):
    # Tags returns empty
    mock_resp_tags = MagicMock()
    mock_resp_tags.json.return_value = {"models": []}
    mock_client.get.return_value = mock_resp_tags
    
    # Mock pull_model
    with patch.object(ollama_manager, "pull_model", new_callable=AsyncMock) as mock_pull:
        await ollama_manager.ensure_model("missing-model")
        mock_pull.assert_called_once_with("missing-model")

@pytest.mark.asyncio
async def test_stop_all_models(mock_client):
    with patch.object(ollama_manager, "get_running_models", new_callable=AsyncMock) as mock_get:
        mock_get.return_value = [{"name": "model1"}]
        await ollama_manager.stop_all_models()
        mock_client.post.assert_called_once_with("/api/generate", json={"model": "model1", "keep_alive": 0})

@pytest.mark.asyncio
async def test_pull_model(mock_client):
    mock_resp = MagicMock()
    mock_resp.raise_for_status = MagicMock()
    
    async def mock_aiter_lines():
        yield '{"status": "pulling"}'
        yield '{"status": "success"}'
        yield 'invalid json'
        yield ''
        
    mock_resp.aiter_lines = mock_aiter_lines
    
    # httpx.AsyncClient.stream is an async context manager
    class MockStreamContextManager:
        async def __aenter__(self):
            return mock_resp
        async def __aexit__(self, exc_type, exc, tb):
            pass

    mock_client.stream.return_value = MockStreamContextManager()
    
    await ollama_manager.pull_model("test-model")
    mock_client.stream.assert_called_with("POST", "/api/pull", json={"name": "test-model"})

@pytest.mark.asyncio
async def test_stream_generate(mock_client):
    mock_resp = MagicMock()
    mock_resp.raise_for_status = MagicMock()
    
    async def mock_aiter_lines():
        yield '{"response": "part1"}'
        yield '{"response": "part2"}'
        
    mock_resp.aiter_lines = mock_aiter_lines
    
    class MockStreamContextManager:
        async def __aenter__(self):
            return mock_resp
        async def __aexit__(self, exc_type, exc, tb):
            pass

    mock_client.stream.return_value = MockStreamContextManager()
    
    chunks = []
    gen = await ollama_manager.generate("test-model", "test", stream=True)
    async for chunk in gen:
        chunks.append(chunk)
        
    assert len(chunks) == 2
    assert chunks[0]["response"] == "part1"
    assert chunks[1]["response"] == "part2"

@pytest.mark.asyncio
async def test_stream_chat(mock_client):
    mock_resp = MagicMock()
    mock_resp.raise_for_status = MagicMock()
    
    async def mock_aiter_lines():
        yield '{"message": {"content": "part1"}}'
        yield '{"message": {"content": "part2"}}'
        
    mock_resp.aiter_lines = mock_aiter_lines
    
    class MockStreamContextManager:
        async def __aenter__(self):
            return mock_resp
        async def __aexit__(self, exc_type, exc, tb):
            pass

    mock_client.stream.return_value = MockStreamContextManager()
    
    chunks = []
    gen = await ollama_manager.chat("test-model", [], stream=True)
    async for chunk in gen:
        chunks.append(chunk)
        
    assert len(chunks) == 2
    assert chunks[0]["message"]["content"] == "part1"

@pytest.mark.asyncio
async def test_preload_model(mock_client):
    await ollama_manager.preload_model("test-model")
    mock_client.post.assert_called_with("/api/generate", json={"model": "test-model", "prompt": "", "keep_alive": -1})

@pytest.mark.asyncio
async def test_unload_model(mock_client):
    await ollama_manager.unload_model("test-model")
    mock_client.post.assert_called_with("/api/generate", json={"model": "test-model", "keep_alive": 0})

@pytest.mark.asyncio
async def test_get_metrics():
    with patch("core.infrastructure.manager.InfrastructureManager.get_system_metrics", return_value={"cpu": 10}):
        metrics = await ollama_manager.get_metrics()
        assert metrics == {"cpu": 10}
