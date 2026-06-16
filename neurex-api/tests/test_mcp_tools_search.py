from unittest.mock import AsyncMock, patch

import pytest

from core.mcp.tools.search import grep_search


@pytest.mark.asyncio
async def test_grep_search_no_rg():
    with patch("shutil.which", return_value=None):
        res = await grep_search("test")
        assert "not installed" in res

@pytest.mark.asyncio
async def test_grep_search_success():
    with patch("shutil.which", return_value="/usr/bin/rg"):
        with patch("asyncio.create_subprocess_exec", new_callable=AsyncMock) as mock_exec:
            mock_proc = AsyncMock()
            mock_proc.communicate.return_value = (b"found line", b"")
            mock_exec.return_value = mock_proc
            
            res = await grep_search("test", ["*.py"])
            assert res == "found line"
            
            # verify call args
            mock_exec.assert_called_once()
            args = mock_exec.call_args.args
            assert "rg" in args
            assert "-g" in args
            assert "*.py" in args
            assert "test" in args

@pytest.mark.asyncio
async def test_grep_search_stderr():
    with patch("shutil.which", return_value="/usr/bin/rg"):
        with patch("asyncio.create_subprocess_exec", new_callable=AsyncMock) as mock_exec:
            mock_proc = AsyncMock()
            mock_proc.communicate.return_value = (b"", b"error details")
            mock_exec.return_value = mock_proc
            
            res = await grep_search("test")
            assert res == ""

@pytest.mark.asyncio
async def test_grep_search_exception():
    with patch("shutil.which", return_value="/usr/bin/rg"):
        with patch("asyncio.create_subprocess_exec", side_effect=Exception("boom")):
            res = await grep_search("test")
            assert "Error executing search: boom" in res
