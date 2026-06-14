import asyncio
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from core.mcp.tools.terminal import _check_allowlist, _check_safety, run_command


def test_check_allowlist():
    # Should pass
    _check_allowlist("ls -la")
    _check_allowlist("pytest tests/")
    
    # Should fail
    with pytest.raises(PermissionError):
        _check_allowlist("rm -rf /")

def test_check_safety():
    assert _check_safety("ls -la")
    assert _check_safety("git status")
    assert not _check_safety("rm -rf /")
    assert not _check_safety("mv a b")
    assert not _check_safety("pytest") # pytest is not in the safe-list check logic (only ls, pwd, git)

@pytest.mark.asyncio
async def test_run_command_approval_required():
    # limited mode with unsafe command
    res = await run_command("rm -rf /", approved=False, autonomy_level="limited")
    assert "APPROVAL_REQUIRED" in res
    assert "potentially unsafe" in res

@pytest.mark.asyncio
async def test_run_command_trash_protection():
    res = await run_command("rm -rf .neurex/trash/file")
    assert "ERROR: Access denied." in res

@pytest.mark.asyncio
async def test_run_command_success(monkeypatch):
    mock_proc = AsyncMock()
    mock_proc.communicate.return_value = (b"hello world", b"")
    mock_proc.returncode = 0
    
    with patch("asyncio.create_subprocess_exec", return_value=mock_proc) as mock_exec:
        res = await run_command("echo hello world", approved=True, autonomy_level="full")
        assert "exit 0" in res
        assert "hello world" in res
        mock_exec.assert_called_once()

@pytest.mark.asyncio
async def test_run_command_timeout(monkeypatch):
    mock_proc = AsyncMock()
    mock_proc.communicate.side_effect = asyncio.TimeoutError
    mock_proc.kill = MagicMock()
    
    with patch("asyncio.create_subprocess_exec", return_value=mock_proc):
        res = await run_command("python -c 'import time; time.sleep(100)'", approved=True)
        assert "timed out" in res
        mock_proc.kill.assert_called_once()

@pytest.mark.asyncio
async def test_wasm_fallback():
    # Simulate Docker Not Found
    with patch("asyncio.create_subprocess_exec", side_effect=FileNotFoundError):
        # Mock the wasm HTTP client
        mock_client_instance = AsyncMock()
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = {"stdout": "wasm out", "exit_code": 0}
        mock_client_instance.post.return_value = mock_resp
        
        with patch("httpx.AsyncClient") as mock_client_cls:
            mock_client_cls.return_value.__aenter__.return_value = mock_client_instance
            res = await run_command("ls", approved=True)
            assert "exit 0" in res
            assert "wasm out" in res
