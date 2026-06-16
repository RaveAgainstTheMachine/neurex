from unittest.mock import AsyncMock, MagicMock

import pytest

from core.context.neural_explorer import NeuralExplorer


@pytest.mark.asyncio
async def test_neural_explorer_hybrid_search():
    mock_ctx = MagicMock()
    mock_ctx.retrieve = AsyncMock(return_value=[
        {"metadata": {"file": "main.py"}, "document": "def main()"}
    ])

    explorer = NeuralExplorer(mock_ctx)
    explorer.update_call_graph("main.py", ["utils.py"])

    # First search: cache miss, retrieves
    results = await explorer.hybrid_search("main", limit=5)
    assert len(results) == 1
    assert results[0]["metadata"]["file"] == "main.py"
    assert mock_ctx.retrieve.call_count == 1

    # Second search: cache hit, no retrieve call
    cached_results = await explorer.hybrid_search("main", limit=5)
    assert cached_results == results
    assert mock_ctx.retrieve.call_count == 1

    # Invalidate cache via update_call_graph
    explorer.update_call_graph("utils.py", [])
    assert len(explorer._search_cache) == 0

    # Third search: cache miss, retrieve call increments
    await explorer.hybrid_search("main", limit=5)
    assert mock_ctx.retrieve.call_count == 2
