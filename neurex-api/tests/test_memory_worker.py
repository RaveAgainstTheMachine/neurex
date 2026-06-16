from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from core.memory.worker import MemoryWorker


@pytest.mark.asyncio
async def test_memory_worker_disabled():
    w = MemoryWorker()
    with patch("asyncio.to_thread", side_effect=Exception("no chromadb")):
        await w.start()
        assert w._enabled is False
        
        # should do nothing
        await w._full_index()
        await w._index_file(Path("test.py"))

@pytest.mark.asyncio
async def test_memory_worker_enabled(tmp_path):
    w = MemoryWorker()
    mock_chroma = MagicMock()
    mock_coll = MagicMock()
    
    mock_chroma_module = MagicMock()
    with patch.dict("sys.modules", {"chromadb": mock_chroma_module}):
        with patch("asyncio.to_thread", new_callable=AsyncMock) as mock_to_thread:
            mock_to_thread.return_value = (mock_chroma, mock_coll)
            with patch("core.memory.embedder.Embedder") as mock_emb:
                with patch("core.memory.summarizer.Summarizer") as mock_sum:
                    # bypass observer
                    with patch("core.memory.worker.Observer") as mock_obs:
                        await w.start()
                        assert w._enabled is True
                        
                        # Test should_index
                        f = tmp_path / "test.py"
                        f.write_text("print('test')")
                        assert w._should_index(f) is True
                        
                        # Missing file
                        assert w._should_index(tmp_path / "missing.py") is False
                        
                        # Ignored dir
                        ignored = tmp_path / ".git" / "test.py"
                        ignored.parent.mkdir()
                        ignored.write_text("test")
                        assert w._should_index(ignored) is False
                        
                        # Test full index
                        with patch.object(w, "_index_file", new_callable=AsyncMock) as mock_index:
                            with patch("core.memory.worker.WORKSPACE_PATH", tmp_path):
                                await w._full_index()
                                mock_index.assert_called()

                        # Test index file
                        with patch("core.memory.chunker.chunk_file") as mock_chunk:
                            mock_chunk.return_value = [{"text": "doc1", "id": "1", "metadata": {}}]
                            
                            mock_emb.return_value.embed_batch = AsyncMock(return_value=[[0.1, 0.2]])
                            
                            async def mock_thread(fn):
                                fn()
                            with patch("asyncio.to_thread", side_effect=mock_thread):
                                await w._index_file(f)
                                mock_coll.upsert.assert_called()
                        
                        await w.stop()
                        mock_obs.return_value.stop.assert_called()
