import asyncio
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from core.languages.lsp_manager import DiagnosticTracker, LSPManager, LSPSession


@pytest.mark.asyncio
async def test_diagnostic_tracker():
    tracker = DiagnosticTracker()
    tracker.update("file:///test/file.py", [{"message": "error"}])
    
    assert len(tracker.get_for_path("/test/file.py")) == 1
    assert tracker.get_count_for_prefix("/test") == 1
    
    tracker.update("file:///test/file.py", [])
    assert len(tracker.get_for_path("/test/file.py")) == 0

@pytest.mark.asyncio
async def test_lsp_session_start_stop():
    session = LSPSession("python", "/tmp/workspace")
    session.cmd = ["mock-lsp"]
    
    with patch("asyncio.create_subprocess_exec", new_callable=AsyncMock) as mock_exec:
        mock_proc = AsyncMock()
        mock_proc.pid = 1234
        mock_exec.return_value = mock_proc
        
        await session.start()
        assert session._running is True
        
        await session.stop()
        assert session._running is False

@pytest.mark.asyncio
async def test_lsp_session_read_loop():
    session = LSPSession("python", "/tmp/workspace")
    session.cmd = ["mock-lsp"]
    
    with patch("asyncio.create_subprocess_exec", new_callable=AsyncMock) as mock_exec:
        mock_proc = AsyncMock()
        mock_proc.pid = 1234
        
        mock_stdout = AsyncMock()
        
        async def mock_read(*args, **kwargs):
            if not getattr(mock_read, "called", False):
                mock_read.called = True
                payload = b'{"jsonrpc":"2.0","method":"textDocument/publishDiagnostics","params":{"uri":"file:///test.py","diagnostics":[]}}'
                return f"Content-Length: {len(payload)}\r\n\r\n".encode() + payload
            else:
                session._running = False
                return b""
                
        mock_stdout.read = mock_read
        mock_proc.stdout = mock_stdout
        mock_exec.return_value = mock_proc
        
        await session.start()
        await asyncio.sleep(0.1) # Wait for read loop
        await session.stop()

@pytest.mark.asyncio
async def test_lsp_session_send_request():
    session = LSPSession("python", "/tmp/workspace")
    session.cmd = ["mock-lsp"]
    
    with patch("asyncio.create_subprocess_exec", new_callable=AsyncMock) as mock_exec:
        mock_proc = AsyncMock()
        mock_stdin = AsyncMock()
        mock_proc.stdin = mock_stdin
        mock_exec.return_value = mock_proc
        
        await session.start()
        
        with patch("asyncio.wait_for", new_callable=AsyncMock) as mock_wait:
            mock_wait.return_value = {"result": "ok"}
            res = await session.send_request("initialize", {})
            assert res == {"result": "ok"}

@pytest.mark.asyncio
async def test_lsp_manager_initialize_workspace():
    mgr = LSPManager()
    
    with patch("core.languages.lsp_manager.LSPManager.get_session", new_callable=AsyncMock) as mock_get:
        with patch("core.languages.lsp_manager.LSPManager.get_supported_languages", return_value=["python"]):
            # Use a safe path
            with patch("os.path.realpath", side_effect=lambda x: x):
                with patch("pathlib.Path.exists", return_value=True):
                    with patch("pathlib.Path.iterdir") as mock_iter:
                        mock_file = MagicMock()
                        mock_file.is_dir.return_value = False
                        mock_file.suffix = ".py"
                        mock_iter.return_value = [mock_file]
                        
                        await mgr.initialize_workspace("/test/workspace")
                        mock_get.assert_called_with("python", "/test/workspace")

@pytest.mark.asyncio
async def test_lsp_manager_install_lsp():
    mgr = LSPManager()
    with patch("core.languages.lsp_manager.LSPManager.get_supported_languages", return_value=[]):
        with patch("asyncio.create_subprocess_shell", new_callable=AsyncMock) as mock_shell:
            mock_proc = AsyncMock()
            mock_proc.returncode = 0
            mock_proc.communicate.return_value = (b"ok", b"")
            mock_shell.return_value = mock_proc
            
            res = await mgr.install_lsp("python")
            assert res is True
            assert mock_shell.called

@pytest.mark.asyncio
async def test_lsp_manager_cleanup():
    mgr = LSPManager()
    mock_session = AsyncMock()
    mgr.sessions["python:/test"] = mock_session
    
    await mgr.cleanup()
    assert mock_session.stop.called
    assert len(mgr.sessions) == 0
