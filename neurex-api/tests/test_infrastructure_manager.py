import asyncio
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from core.infrastructure.manager import InfrastructureManager


@pytest.fixture
def manager():
    return InfrastructureManager()

@pytest.mark.asyncio
async def test_get_status_ollama(manager):
    with patch.object(manager, '_is_process_running', AsyncMock(return_value=True)):
        with patch.object(manager, '_get_version', AsyncMock(return_value="v1.0.0")):
            with patch('shutil.which', return_value="/bin/ollama"):
                res = await manager.get_status()
                ollama_status = next(s for s in res if s["name"] == "ollama")
                assert ollama_status["status"] == "running"
                assert ollama_status["version"] == "v1.0.0"

@pytest.mark.asyncio
async def test_stop_engine(manager):
    mock_proc = MagicMock()
    mock_proc.info = {"name": "ollama"}
    
    with patch('psutil.process_iter', return_value=[mock_proc]):
        res = await manager.stop_engine("ollama")
        assert res is True
        mock_proc.terminate.assert_called_once()

def test_get_hardware_specs(manager):
    with patch('psutil.cpu_count', return_value=8):
        with patch('platform.system', return_value="Linux"):
            res = manager.get_hardware_specs()
            assert res["cpu_cores"] == 8

@pytest.mark.asyncio
async def test_pull_model_ollama(manager):
    with patch('shutil.which', return_value="/bin/ollama"):
        with patch('core.settings.manager.settings_manager.get', return_value="/tmp/models"):
            mock_proc = AsyncMock()
            mock_proc.communicate.return_value = (b"", b"")
            mock_proc.returncode = 0
            with patch('asyncio.create_subprocess_exec', return_value=mock_proc):
                res = await manager.pull_model("ollama", "llama3")
                assert res is True

@pytest.mark.asyncio
async def test_install_engine_vllm(manager):
    mock_proc = AsyncMock()
    mock_proc.communicate.return_value = (b"", b"")
    mock_proc.returncode = 0
    mock_proc.wait = AsyncMock()
    with patch('asyncio.create_subprocess_exec', return_value=mock_proc):
        with patch('asyncio.create_subprocess_shell', return_value=mock_proc):
            res = await manager.install_engine("vllm")
            assert res is True

def test_get_system_vram_nvidia(manager):
    mock_res = MagicMock()
    mock_res.stdout = "8192\n"
    mock_res.returncode = 0
    with patch('subprocess.run', return_value=mock_res):
        res = manager.get_system_vram()
        assert res == 8.0

def test_get_system_metrics(manager):
    with patch.object(manager, 'get_system_vram', return_value=8.0):
        with patch.object(manager, 'validate_storage_permissions', return_value={}):
            with patch.object(manager, 'get_hardware_specs', return_value={}):
                with patch('psutil.virtual_memory') as mock_vm:
                    mock_vm.return_value.total = 16 * 1024**3
                    mock_vm.return_value.used = 8 * 1024**3
                    mock_vm.return_value.available = 8 * 1024**3
                    mock_vm.return_value.percent = 50.0
                    with patch('core.settings.manager.settings_manager.get', return_value=[]):
                        res = manager.get_system_metrics()
                        assert res["vram_gb"] == 8.0
                        assert res["ram_total_gb"] == 16.0

@pytest.mark.asyncio
async def test_get_status_llamacpp(manager):
    with patch("importlib.util.find_spec") as mock_spec:
        mock_spec.return_value.origin = "/dummy/path"
        with patch.object(manager, "_is_process_running", AsyncMock(return_value=False)):
            with patch.object(manager, "_get_version", AsyncMock(return_value="unknown")):
                res = await manager.get_status()
                llama_status = next(s for s in res if s["name"] == "llama.cpp")
                assert llama_status["status"] == "stopped"
                assert llama_status["installed"] is True

@pytest.mark.asyncio
async def test_start_engine_ollama(manager):
    with patch("shutil.which", return_value="/bin/ollama"):
        with patch("core.settings.manager.settings_manager.get") as mock_get:
            mock_get.side_effect = lambda k: "11434" if k == "ollama_port" else "/tmp"
            with patch("asyncio.create_subprocess_exec", return_value=AsyncMock()) as mock_exec:
                res = await manager.start_engine("ollama")
                assert res is True
                mock_exec.assert_called_once()

@pytest.mark.asyncio
async def test_install_engine_ollama(manager):
    with patch("asyncio.create_subprocess_exec") as mock_exec:
        mock_proc = AsyncMock()
        mock_proc.wait.return_value = 0
        mock_proc.returncode = 0
        mock_exec.return_value = mock_proc
        
        with patch("asyncio.create_subprocess_shell") as mock_shell:
            mock_shell_proc = AsyncMock()
            mock_shell_proc.communicate.return_value = (b"", b"")
            mock_shell_proc.returncode = 0
            mock_shell.return_value = mock_shell_proc
            
            res = await manager.install_engine("ollama")
            assert res is True
            mock_shell.assert_called_with("curl -fsSL https://ollama.com/install.sh | sh", stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE)

@pytest.mark.asyncio
async def test_resolve_model_params(manager):
    with patch.object(manager, "get_installed_models", AsyncMock()) as mock_get:
        mock_get.return_value = [{"name": "llama3:8b", "params": "8B"}]
        
        res = await manager.resolve_model_params("llama3:8b")
        assert res == "8B"
        
        # fallback regex
        res2 = await manager.resolve_model_params("unknown-14b")
        assert res2 == "14B"

@pytest.mark.asyncio
async def test_is_process_running_ollama(manager):
    mock_proc = MagicMock()
    mock_proc.info = {"name": "ollama"}
    with patch("psutil.process_iter", return_value=[mock_proc]):
        class MockResponse:
            status = 200
        class MockSession:
            async def __aenter__(self): return self
            async def __aexit__(self, *args): pass
            def get(self, *args, **kwargs):
                class MockGet:
                    async def __aenter__(self): return MockResponse()
                    async def __aexit__(self, *args): pass
                return MockGet()
                
        with patch("aiohttp.ClientSession", return_value=MockSession()):
            res = await manager._is_process_running("ollama")
            assert res is True
