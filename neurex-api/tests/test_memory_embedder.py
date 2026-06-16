from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from core.memory.embedder import Embedder, Reranker


@pytest.mark.asyncio
async def test_embed_success():
    with patch("httpx.AsyncClient.post", new_callable=AsyncMock) as mock_post:
        mock_res = MagicMock()
        mock_res.json.return_value = {"embedding": [0.1, 0.2]}
        mock_post.return_value = mock_res
        
        e = Embedder()
        res = await e.embed("test")
        assert res == [0.1, 0.2]

@pytest.mark.asyncio
async def test_embed_batch_success():
    with patch("httpx.AsyncClient.post", new_callable=AsyncMock) as mock_post:
        mock_res = MagicMock()
        mock_res.json.return_value = {"embedding": [0.1, 0.2]}
        mock_post.return_value = mock_res
        
        e = Embedder()
        res = await e.embed_batch(["test1", "test2"])
        assert len(res) == 2
        assert res[0] == [0.1, 0.2]

@pytest.mark.asyncio
async def test_embed_exception():
    with patch("httpx.AsyncClient.post", side_effect=Exception("boom")):
        e = Embedder()
        res = await e.embed("test")
        assert len(res) == 768
        assert res[0] == 0.0
        
def test_reranker_success():
    r = Reranker()
    with patch.object(r, "_load") as mock_load:
        mock_model = MagicMock()
        mock_model.predict.return_value = [0.9, 0.1]
        mock_load.return_value = mock_model
        
        cands = [{"document": "d1"}, {"document": "d2"}]
        res = r.rerank("q", cands, top_k=1)
        assert len(res) == 1
        assert res[0]["document"] == "d1"

def test_reranker_no_model():
    r = Reranker()
    with patch.object(r, "_load", return_value=None):
        cands = [{"document": "d1"}, {"document": "d2"}]
        res = r.rerank("q", cands, top_k=1)
        assert len(res) == 1
        assert res[0]["document"] == "d1"

def test_reranker_exception():
    r = Reranker()
    with patch.object(r, "_load") as mock_load:
        mock_model = MagicMock()
        mock_model.predict.side_effect = Exception("boom")
        mock_load.return_value = mock_model
        
        cands = [{"document": "d1"}, {"document": "d2"}]
        res = r.rerank("q", cands, top_k=1)
        assert len(res) == 1
        assert res[0]["document"] == "d1"

import sys


def test_reranker_load():
    mock_torch = MagicMock()
    mock_torch.cuda.is_available.return_value = False
    mock_st = MagicMock()
    mock_ce = MagicMock()
    mock_st.CrossEncoder = mock_ce
    
    with patch.dict(sys.modules, {"torch": mock_torch, "sentence_transformers": mock_st}):
        r = Reranker()
        model = r._load()
        assert model is not None
        mock_ce.assert_called_once()
        
        # test cached
        model2 = r._load()
        assert model2 is model
        assert mock_ce.call_count == 1
