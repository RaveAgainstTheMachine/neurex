from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from core.languages.lsp_manager import DiagnosticTracker, LSPSession, lsp_manager


@pytest.mark.asyncio
async def test_diagnostic_tracker():
    tracker = DiagnosticTracker()
    tracker.update("file:///test/file.py", [{"message": "error"}])
    res = tracker.get_for_path("/test/file.py")
    assert len(res) == 1
    assert res[0]["message"] == "error"
    
    count = tracker.get_count_for_prefix("/test")
    assert count == 1

@pytest.mark.asyncio
async def test_lsp_session_lifecycle(monkeypatch):
    session = LSPSession("python", "/workspace")
    
    mock_proc = AsyncMock()
    mock_proc.pid = 1234
    mock_proc.stdout = AsyncMock()
    mock_proc.stdout.read.return_value = b"" # trigger read_loop exit
    mock_proc.stdin = AsyncMock()
    mock_proc.wait = AsyncMock()
    
    with patch("asyncio.create_subprocess_exec", return_value=mock_proc):
        await session.start()
        assert session._running
        assert session.process == mock_proc
        
        await session.stop()
        assert not session._running
        mock_proc.terminate.assert_called_once()

@pytest.mark.asyncio
async def test_lsp_session_handle_json():
    session = LSPSession("python", "/workspace")
    body = b'{"method": "textDocument/publishDiagnostics", "params": {"uri": "file:///workspace/test.py", "diagnostics": [{"msg": "err"}]}}'
    
    with patch("core.languages.lsp_manager.diagnostic_tracker.update") as mock_update:
        session.handle_json(body)
        mock_update.assert_called_once_with("file:///workspace/test.py", [{"msg": "err"}])

@pytest.mark.asyncio
async def test_lsp_manager_get_supported():
    with patch.object(lsp_manager, "_find_executable", return_value="/bin/dummy"):
        supported = lsp_manager.get_supported_languages()
        assert "python" in supported

@pytest.mark.asyncio
async def test_lsp_manager_install(monkeypatch):
    mock_proc = AsyncMock()
    mock_proc.communicate.return_value = (b"", b"")
    mock_proc.returncode = 0
    
    with patch("asyncio.create_subprocess_shell", return_value=mock_proc):
        res = await lsp_manager.install_lsp("python") # already has recipe
        assert res

@pytest.mark.asyncio
async def test_lsp_manager_get_session(tmp_path):
    (tmp_path / ".git").mkdir()
    
    with patch("api.routes.files.get_workspace", return_value=str(tmp_path)):
        with patch.object(lsp_manager, "_find_executable", return_value="/bin/python"):
            with patch.object(lsp_manager, "get_supported_languages", return_value=["python"]):
                mock_proc = AsyncMock()
                mock_proc.pid = 123
                mock_proc.stdout = AsyncMock()
                mock_proc.stdout.read.return_value = b""
                with patch("asyncio.create_subprocess_exec", return_value=mock_proc):
                    session = await lsp_manager.get_session("python", str(tmp_path))
                    assert session.lang == "python"
                    assert "python" in session.cmd[0]
                    
                    # Retrieve existing
                    session2 = await lsp_manager.get_session("python", str(tmp_path))
                    assert session is session2

@pytest.mark.asyncio
async def test_lsp_session_send_request():
    session = LSPSession("python", "/tmp")
    session._running = True
    session.process = AsyncMock()
    session.process.stdin.write = MagicMock()
    
    async def mock_wait_for(fut, t):
        return {"id": 1, "result": "ok"}
        
    with patch("asyncio.wait_for", side_effect=mock_wait_for):
        res = await session.send_request("testMethod", {})
        assert res["result"] == "ok"

@pytest.mark.asyncio
async def test_lsp_manager_initialize_workspace(tmp_path):
    (tmp_path / "test.py").write_text("print('test')")
    
    with patch("api.routes.files.get_workspace", return_value=str(tmp_path)):
        with patch.object(lsp_manager, "get_supported_languages", return_value=["python"]):
            with patch.object(lsp_manager, "get_session", AsyncMock()) as mock_get_session:
                await lsp_manager.initialize_workspace(str(tmp_path))
                mock_get_session.assert_called_once()
