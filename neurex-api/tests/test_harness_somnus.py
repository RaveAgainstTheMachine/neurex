import time
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from core.harness.somnus import somnus_daemon


@pytest.fixture(autouse=True)
def reset_daemon():
    # Reset singleton state before each test
    somnus_daemon.is_running = False
    somnus_daemon.last_run = 0
    somnus_daemon.ws = None

def test_somnus_daemon_lifecycle():
    assert somnus_daemon.is_running is False
    somnus_daemon.start("/mock/workspace")
    assert somnus_daemon.is_running is True
    assert somnus_daemon.ws == "/mock/workspace"
    
    # Starting again should no-op
    somnus_daemon.start("/other/workspace")
    assert somnus_daemon.ws == "/mock/workspace"

    somnus_daemon.stop()
    assert somnus_daemon.is_running is False

@pytest.mark.asyncio
async def test_somnus_daemon_on_change():
    somnus_daemon.start("/mock/workspace")
    somnus_daemon.cooldown = 10
    
    # Case 1: Non-relevant path (.git)
    with patch.object(somnus_daemon, "dream", new_callable=AsyncMock) as mock_dream:
        await somnus_daemon.on_change([".git/config"])
        mock_dream.assert_not_called()

    # Case 2: Relevant path, cooldown active (last_run is close to now)
    somnus_daemon.last_run = time.time()
    with patch.object(somnus_daemon, "dream", new_callable=AsyncMock) as mock_dream:
        await somnus_daemon.on_change(["src/main.py"])
        mock_dream.assert_not_called()

    # Case 3: Relevant path, cooldown expired
    somnus_daemon.last_run = 0
    with patch.object(somnus_daemon, "dream", new_callable=AsyncMock) as mock_dream:
        await somnus_daemon.on_change(["src/main.py"])
        mock_dream.assert_called_once()
        assert somnus_daemon.last_run > 0

@pytest.mark.asyncio
async def test_somnus_daemon_dream():
    somnus_daemon.start("/mock/workspace")
    
    with patch("core.settings.manager.settings_manager.get", return_value="high"):
        with patch("core.harness.somnus.synthesize_project_intel", new_callable=AsyncMock) as mock_intel:
            with patch("core.context.skeptical_memory.SkepticalMemory") as mock_mem_class:
                mock_memory = MagicMock()
                mock_mem_class.return_value = mock_memory
                
                with patch("core.skills.harvester.harvester.harvest_from_mesh", new_callable=AsyncMock) as mock_harvest:
                    await somnus_daemon.dream()
                    mock_intel.assert_called_once()
                    mock_memory.update_memory.assert_called_once()
                    mock_harvest.assert_called_once()
