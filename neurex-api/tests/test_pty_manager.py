import asyncio
from unittest.mock import MagicMock, patch

import pytest

from core.terminal.pty_manager import PTYManager


@pytest.fixture
def pty_manager():
    manager = PTYManager()
    manager.close_all()
    return manager

def test_pty_manager_singleton():
    m1 = PTYManager()
    m2 = PTYManager()
    assert m1 is m2

@pytest.mark.asyncio
async def test_pty_manager_create_and_close(pty_manager):
    with patch("core.terminal.pty_manager.PtyProcessUnicode.spawn") as mock_spawn:
        mock_proc = MagicMock()
        mock_proc.pid = 1234
        mock_proc.isalive.return_value = True
        mock_spawn.return_value = mock_proc
        
        session = pty_manager.get_or_create_session("sess1")
        assert session.session_id == "sess1"
        assert "sess1" in pty_manager.sessions
        
        # Test close session
        pty_manager.close_session("sess1")
        assert "sess1" not in pty_manager.sessions
        mock_proc.terminate.assert_called_with(force=True)

@pytest.mark.asyncio
async def test_pty_manager_get_existing(pty_manager):
    with patch("core.terminal.pty_manager.PtyProcessUnicode.spawn"):
        session = pty_manager.get_or_create_session("sess1", rows=20, cols=80)
        
        with patch.object(session, "write") as mock_write:
            with patch.object(session, "resize") as mock_resize:
                session2 = pty_manager.get_or_create_session("sess1", rows=30, cols=100)
                assert session is session2
                mock_resize.assert_called_with(30, 100)

@pytest.mark.asyncio
async def test_pty_session_broadcast(pty_manager):
    with patch("core.terminal.pty_manager.PtyProcessUnicode.spawn"):
        session = pty_manager.get_or_create_session("sess1")
        
        results = []
        def listener(data):
            results.append(data)
            
        session.attach(listener)
        session._broadcast("hello")
        session._broadcast(" world")
        
        assert results == ["hello", " world"]
        assert session.history == "hello world"
        
        session.detach(listener)
        session._broadcast(" detached")
        assert len(results) == 2

@pytest.mark.asyncio
async def test_pty_session_write(pty_manager):
    with patch("core.terminal.pty_manager.PtyProcessUnicode.spawn") as mock_spawn:
        mock_proc = MagicMock()
        mock_proc.isalive.return_value = True
        mock_spawn.return_value = mock_proc
        
        session = pty_manager.get_or_create_session("sess1")
        session.write("ls\n")
        
        mock_proc.write.assert_called_with("ls\n")

@pytest.mark.asyncio
async def test_pty_session_propose_command(pty_manager):
    with patch("core.terminal.pty_manager.PtyProcessUnicode.spawn"):
        session = pty_manager.get_or_create_session("sess1")
        
        async def mock_broadcast(*args, **kwargs):
            fut = session.pending_approvals.get("task1")
            if fut and not fut.done():
                fut.set_result(True)
                
        with patch("core.collaboration.presence.presence_manager.broadcast", side_effect=mock_broadcast):
            approved = await session.propose_and_await_approval("rm -rf /", "task1")
            assert approved is True

@pytest.mark.asyncio
async def test_pty_session_execute_command(pty_manager):
    with patch("core.terminal.pty_manager.PtyProcessUnicode.spawn"):
        session = pty_manager.get_or_create_session("sess1")
        session.write = MagicMock()
        
        async def fake_output():
            await asyncio.sleep(0.01)
            session._broadcast("command output\n")
            session._broadcast("PTY_CMD_FINISHED__task1__:0\n")
            
        asyncio.create_task(fake_output())
        
        code, out = await session.execute_command_in_pty("echo ok", "task1")
        assert code == 0
        assert "command output" in out
