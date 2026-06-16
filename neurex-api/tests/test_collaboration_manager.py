from datetime import UTC, datetime, timedelta
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from core.collaboration.manager import CollaborationManager
from core.task_graph import FileLock


@pytest.fixture
def manager():
    return CollaborationManager()

@pytest.fixture
def mock_session():
    session = AsyncMock()
    with patch("core.collaboration.manager.async_session", return_value=session):
        yield session

@pytest.mark.asyncio
async def test_acquire_lock_new(manager, mock_session):
    mock_session.get.return_value = None
    
    with patch("core.collaboration.manager.presence_manager.broadcast") as mock_broadcast:
        res = await manager.acquire_lock("/test.txt", "user1", conversation_id="conv1")
        assert res is True
        mock_session.add.assert_called_once()
        mock_session.commit.assert_called()
        mock_broadcast.assert_called_once()

@pytest.mark.asyncio
async def test_acquire_lock_existing_denied(manager, mock_session):
    now = datetime.now(UTC)
    existing_lock = FileLock(path="/test.txt", locked_by="user2", owner_node="node1", expires_at=now + timedelta(seconds=100))
    mock_session.get.return_value = existing_lock
    
    res = await manager.acquire_lock("/test.txt", "user1")
    assert res is False

@pytest.mark.asyncio
async def test_acquire_lock_existing_expired_or_owned(manager, mock_session):
    now = datetime.now(UTC)
    # Owned by same user
    existing_lock = FileLock(path="/test.txt", locked_by="user1", owner_node="node1", expires_at=now + timedelta(seconds=100))
    mock_session.get.return_value = existing_lock
    
    res = await manager.acquire_lock("/test.txt", "user1")
    assert res is True
    mock_session.delete.assert_called_once_with(existing_lock)

@pytest.mark.asyncio
async def test_release_lock(manager, mock_session):
    existing_lock = FileLock(path="/test.txt", locked_by="user1", owner_node="node1", expires_at=datetime.now(UTC))
    mock_session.get.return_value = existing_lock
    
    with patch("core.collaboration.manager.presence_manager.broadcast") as mock_broadcast:
        res = await manager.release_lock("/test.txt", "user1", "conv1")
        assert res is True
        mock_session.delete.assert_called_once_with(existing_lock)
        mock_broadcast.assert_called_once()
        
    # Test release by wrong user
    mock_session.delete.reset_mock()
    res2 = await manager.release_lock("/test.txt", "user2")
    assert res2 is False
    mock_session.delete.assert_not_called()

@pytest.mark.asyncio
async def test_get_active_locks(manager, mock_session):
    mock_result = MagicMock()
    mock_result.all.return_value = ["lock1"]
    mock_session.exec.return_value = mock_result
    
    locks = await manager.get_active_locks()
    assert locks == ["lock1"]
