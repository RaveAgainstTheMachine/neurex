from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi import Request

from core.infrastructure.insomnia import InsomniaService
from core.infrastructure.logging_middleware import DebugLoggingMiddleware
from core.infrastructure.maintenance import PredictiveMaintenance


def test_insomnia_service():
    service = InsomniaService()
    
    with patch("core.settings.manager.settings_manager.get", return_value=True):
        with patch("wakelock.lock") as mock_lock:
            service.sync()
            mock_lock.assert_called_once()
            assert service.is_active is True

    # Call sync again when active: no-op
    with patch("core.settings.manager.settings_manager.get", return_value=True):
        with patch("wakelock.lock") as mock_lock:
            service.sync()
            mock_lock.assert_not_called()

    # Toggle off
    with patch("core.settings.manager.settings_manager.get", return_value=False):
        with patch("wakelock.unlock") as mock_unlock:
            service.sync()
            mock_unlock.assert_called_once()
            assert service.is_active is False

def test_insomnia_service_exceptions():
    service = InsomniaService()
    
    # Lock exception
    with patch("core.settings.manager.settings_manager.get", return_value=True):
        with patch("wakelock.lock", side_effect=Exception("Failed lock")):
            service.sync()
            assert service.is_active is False

    # Unlock exception
    service.is_active = True
    with patch("core.settings.manager.settings_manager.get", return_value=False):
        with patch("wakelock.unlock", side_effect=Exception("Failed unlock")):
            service.sync()
            assert service.is_active is True

@pytest.mark.asyncio
async def test_debug_logging_middleware():
    middleware = DebugLoggingMiddleware(app=None)
    
    # Mock Starlette/FastAPI request
    scope = {
        "type": "http",
        "method": "GET",
        "path": "/test-path",
        "headers": [(b"host", b"localhost"), (b"x-test", b"value")],
    }
    request = Request(scope=scope)
    
    mock_response = MagicMock()
    mock_response.status_code = 200
    
    call_next = AsyncMock(return_value=mock_response)
    
    with patch("core.infrastructure.logging_middleware.logger") as mock_logger:
        res = await middleware.dispatch(request, call_next)
        assert res == mock_response
        assert mock_logger.info.call_count == 3

@pytest.mark.asyncio
async def test_predictive_maintenance():
    service = PredictiveMaintenance()
    
    # 1. report churn under threshold
    await service.report_churn(["a.py", "b.py"])
    assert len(service.churn_buffer) == 2
    
    # 2. report churn over threshold
    service.churn_threshold = 3
    
    with patch.object(service, "trigger_maintenance_task", new_callable=AsyncMock) as mock_trigger:
        await service.report_churn(["c.py"])
        # trigger should be scheduled
        mock_trigger.assert_called_once()

@pytest.mark.asyncio
async def test_trigger_maintenance_task():
    service = PredictiveMaintenance()
    service.churn_buffer.add("temp.py")
    
    with patch("core.memory.worker.memory_worker") as mock_worker:
        mock_worker._enabled = True
        mock_worker._full_index = AsyncMock()
        
        await service.trigger_maintenance_task()
        
        assert len(service.churn_buffer) == 0
        mock_worker._full_index.assert_called_once()

    # If memory worker disabled
    service.churn_buffer.add("temp.py")
    with patch("core.memory.worker.memory_worker") as mock_worker:
        mock_worker._enabled = False
        await service.trigger_maintenance_task()
        assert len(service.churn_buffer) == 0
