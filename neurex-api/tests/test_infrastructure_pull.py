from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from core.infrastructure.manager import InfrastructureManager


@pytest.mark.asyncio
async def test_pull_model_ollama():
    mgr = InfrastructureManager()
    with patch("shutil.which", return_value="/usr/bin/ollama"):
        with patch("core.settings.manager.settings_manager.get", return_value="/tmp/models"):
            with patch("asyncio.create_subprocess_exec", new_callable=AsyncMock) as mock_exec:
                mock_proc = AsyncMock()
                mock_proc.communicate.return_value = (b"ok", b"")
                mock_proc.returncode = 0
                mock_exec.return_value = mock_proc
                
                res = await mgr.pull_model("ollama", "llama3")
                assert res is True
                mock_exec.assert_called()

@pytest.mark.asyncio
async def test_pull_model_ollama_missing():
    mgr = InfrastructureManager()
    with patch("shutil.which", return_value=None):
        with pytest.raises(Exception, match="Ollama not installed"):
            await mgr.pull_model("ollama", "llama3")

@pytest.mark.asyncio
async def test_pull_model_llama_cpp(tmp_path):
    mgr = InfrastructureManager()
    with patch("core.settings.manager.settings_manager.get", return_value=str(tmp_path)):
        with patch("huggingface_hub.hf_hub_download", return_value="/tmp/model.gguf") as mock_hf:
            with patch("huggingface_hub.HfApi") as mock_api:
                mock_api_inst = MagicMock()
                mock_api_inst.list_repo_files.return_value = ["model.gguf", "readme.md"]
                mock_api.return_value = mock_api_inst
                
                res = await mgr.pull_model("llama.cpp", "TheBloke/llama")
                assert res is True
                mock_hf.assert_called()

@pytest.mark.asyncio
async def test_pull_model_llama_cpp_no_gguf(tmp_path):
    mgr = InfrastructureManager()
    with patch("core.settings.manager.settings_manager.get", return_value=str(tmp_path)):
        with patch("huggingface_hub.HfApi") as mock_api:
            mock_api_inst = MagicMock()
            mock_api_inst.list_repo_files.return_value = ["readme.md"]
            mock_api.return_value = mock_api_inst
            
            with pytest.raises(Exception, match="No .gguf file found"):
                await mgr.pull_model("llama.cpp", "TheBloke/llama")

@pytest.mark.asyncio
async def test_pull_model_unsupported():
    mgr = InfrastructureManager()
    with pytest.raises(Exception, match="is not supported"):
        await mgr.pull_model("vllm", "llama3")

@pytest.mark.asyncio
async def test_start_engine_ollama():
    mgr = InfrastructureManager()
    with patch("shutil.which", return_value="/usr/bin/ollama"):
        with patch("core.settings.manager.settings_manager.get", side_effect=lambda x: "11434" if x == "ollama_port" else "/tmp"):
            with patch("asyncio.create_subprocess_exec", new_callable=AsyncMock) as mock_exec:
                res = await mgr.start_engine("ollama")
                assert res is True

@pytest.mark.asyncio
async def test_start_engine_vllm():
    mgr = InfrastructureManager()
    with patch("core.settings.manager.settings_manager.get", return_value="8000"):
        with patch("core.infrastructure.vram_pool.vram_pool.get_effective_context_tokens", return_value=4096):
            with patch("asyncio.create_subprocess_exec", new_callable=AsyncMock) as mock_exec:
                res = await mgr.start_engine("vllm")
                assert res is True

@pytest.mark.asyncio
async def test_start_engine_llama_cpp():
    mgr = InfrastructureManager()
    with patch("core.settings.manager.settings_manager.get", return_value="8080"):
        with patch("core.infrastructure.vram_pool.vram_pool.get_effective_context_tokens", return_value=4096):
            with patch("asyncio.create_subprocess_exec", new_callable=AsyncMock) as mock_exec:
                res = await mgr.start_engine("llama.cpp")
                assert res is True

@pytest.mark.asyncio
async def test_install_engine_ollama():
    mgr = InfrastructureManager()
    with patch("asyncio.create_subprocess_exec", new_callable=AsyncMock) as mock_exec:
        mock_proc = AsyncMock()
        mock_proc.returncode = 0
        mock_exec.return_value = mock_proc
        with patch("asyncio.create_subprocess_shell", new_callable=AsyncMock) as mock_shell:
            mock_shell_proc = AsyncMock()
            mock_shell_proc.communicate.return_value = (b"ok", b"")
            mock_shell_proc.returncode = 0
            mock_shell.return_value = mock_shell_proc
            
            res = await mgr.install_engine("ollama")
            assert res is True

@pytest.mark.asyncio
async def test_get_status():
    mgr = InfrastructureManager()
    with patch.object(mgr, "_is_process_running", new_callable=AsyncMock, return_value=True):
        with patch.object(mgr, "_get_version", new_callable=AsyncMock, return_value="1.0"):
            with patch("shutil.which", return_value="/bin/ollama"):
                # need to mock importlib for llama.cpp
                with patch("importlib.util.find_spec") as mock_find:
                    mock_spec = MagicMock()
                    mock_spec.origin = "/path/to/llama"
                    mock_find.return_value = mock_spec
                    
                    res = await mgr.get_status()
                    assert len(res) == 3
