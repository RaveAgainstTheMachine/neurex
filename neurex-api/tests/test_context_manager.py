from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from core.context.manager import ContextManager


@pytest.fixture
def manager():
    return ContextManager()

def test_get_budgets(manager):
    res = manager.get_budgets(hardware_context=8000)
    assert res["CONTEXT_WINDOW"] == 8000
    assert res["SYSTEM_BUDGET"] == 800
    assert res["RAG_BUDGET"] == 2000
    assert res["TOOL_OUTPUT_MAX"] == 800
    assert res["HISTORY_BUDGET"] == 2800

def test_get_budgets_fallback(manager):
    with patch("core.settings.manager.settings_manager.get", return_value=10000):
        res = manager.get_budgets()
        assert res["CONTEXT_WINDOW"] == 10000

def test_get_collection(manager):
    with patch("chromadb.PersistentClient") as mock_client:
        mock_chroma = MagicMock()
        mock_client.return_value = mock_chroma
        collection = manager._get_collection()
        mock_chroma.get_or_create_collection.assert_called_with("neurex_codebase")
        assert manager._available is True

@pytest.mark.asyncio
async def test_retrieve(manager):
    mock_embedder = AsyncMock()
    mock_embedder.embed.return_value = [0.1, 0.2]
    manager._embedder = mock_embedder
    
    with patch("os.environ.get", return_value="false"):
        with patch.object(manager, "_get_collection") as mock_get_coll:
            mock_coll = MagicMock()
            mock_coll.query.return_value = {
                "documents": [["doc1", "doc2"]],
                "metadatas": [[{"id": 1}, {"id": 2}]],
                "distances": [[0.1, 0.2]]
            }
            mock_get_coll.return_value = mock_coll
            
            with patch.object(manager, "get_budgets", return_value={"RAG_BUDGET": 1000}):
                with patch("core.context.manager.os.getenv", return_value="false"):
                    res = await manager.retrieve("test query")
                    assert len(res) == 2
                    assert res[0]["document"] == "doc1"

def test_trim_history(manager):
    with patch.object(manager, "get_budgets", return_value={"HISTORY_BUDGET": 50}):
        manager.count_tokens = MagicMock(return_value=10) # 10 tokens per message
        messages = [
            {"role": "system", "content": "sys"},
            {"role": "user", "content": "u1"},
            {"role": "assistant", "content": "a1"},
            {"role": "user", "content": "u2"},
            {"role": "assistant", "content": "a2"},
            {"role": "user", "content": "u3"},
            {"role": "assistant", "content": "a3"},
        ]
        # Total tokens = 70. Budget = 50. Needs trimming.
        trimmed = manager.trim_history(messages)
        # Should drop first two history msgs (u1, a1)
        assert len(trimmed) == 5
        assert trimmed[0]["role"] == "system"
        assert trimmed[1]["content"] == "u2"

def test_truncate_tool_output(manager):
    with patch.object(manager, "get_budgets", return_value={"TOOL_OUTPUT_MAX": 5}):
        manager.count_tokens = MagicMock(return_value=10)
        res = manager.truncate_tool_output("very long output string")
        assert res.endswith("[truncated]")

def test_count_tokens(manager):
    if manager._enc:
        manager._enc.encode = MagicMock(return_value=[1, 2, 3])
        assert manager.count_tokens("test") == 3
    else:
        assert manager.count_tokens("test") == 1 # len(4)//4
