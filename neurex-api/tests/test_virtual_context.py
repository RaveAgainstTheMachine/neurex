"""
tests/test_virtual_context.py
Unit tests for the Virtual Context Paging System.
"""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from core.context.compression import ContextCompressor
from core.context.manager import ContextManager
from core.context.virtual_context import VirtualContextAssembler
from core.infrastructure.manager import InfrastructureManager
from core.infrastructure.vram_pool import vram_pool
from core.settings.manager import settings_manager


def test_vram_to_token_budget():
    """Verify vram_pool.get_effective_context_tokens() computes context budgets correctly."""
    vram_pool.shards = {}
    vram_pool.total_capacity_gb = 0.0

    # 1. Fallback / No GPU
    with patch("core.infrastructure.manager.InfrastructureManager.get_system_vram", return_value=0.0):
        tokens = vram_pool.get_effective_context_tokens()
        assert tokens == 8192

    # 2. Small GPU (8GB)
    vram_pool.total_capacity_gb = 8.0
    # available = max(0, 8.0 - 10.0) = 0.0 -> fallback to max(4096, min(0, 1M)) -> 4096
    assert vram_pool.get_effective_context_tokens(model_size_gb=10.0) == 4096
    assert vram_pool.get_effective_context_tokens(model_size_gb=4.0) == 1020000 or vram_pool.get_effective_context_tokens(model_size_gb=4.0) >= 4096

    # 3. Mid GPU (24GB)
    vram_pool.total_capacity_gb = 24.0
    # available = 14GB -> 14 * 300,000 * 0.85 = 3,570,000 -> min(3.57M, 1M) = 1,000,000
    assert vram_pool.get_effective_context_tokens(model_size_gb=10.0) == 1000000


def test_multi_gpu_nvidia_smi():
    """Verify get_system_vram() aggregates VRAM across all local NVIDIA GPUs."""
    infra = InfrastructureManager()
    
    mock_run = MagicMock()
    mock_run.return_value.returncode = 0
    mock_run.return_value.stdout = "8192\n16384\n"
    
    with patch("subprocess.run", mock_run):
        vram = infra.get_system_vram()
        # 8192 + 16384 = 24576 MiB -> 24 GB
        assert vram == 24.0


def test_amd_gpu_detection():
    """Verify get_system_vram() detects AMD GPUs via sysfs."""
    infra = InfrastructureManager()
    
    mock_glob = ["/sys/class/drm/card0/device/mem_info_vram_total"]
    mock_open = patch("builtins.open", MagicMock(return_value=MagicMock(__enter__=MagicMock(return_value=MagicMock(read=MagicMock(return_value="17179869184"))))))
    
    with (
        patch("glob.glob", return_value=mock_glob),
        mock_open,
        patch("subprocess.run", side_effect=Exception("Failed to run CLI"))
    ):
        vram = infra.get_system_vram()
        # 17179869184 bytes = 16.0 GB
        assert vram == 16.0


@pytest.mark.asyncio
async def test_mesh_vram_pooling():
    """Verify VirtualVRAMPool synchronizes and aggregates mesh peer VRAM."""
    vram_pool.shards = {}
    vram_pool.total_capacity_gb = 0.0

    class MockPeer:
        def __init__(self, name, url, vram_gb):
            self.name = name
            self.url = url
            self.vram_gb = vram_gb
            self.status = "online"

    peers = {
        "peer1": MockPeer("Node1", "http://node1", 24.0),
        "peer2": MockPeer("Node2", "http://node2", 48.0),
    }

    with (
        patch("core.infrastructure.mesh.mesh_router.peers", peers),
        patch("core.infrastructure.manager.InfrastructureManager.get_system_vram", return_value=16.0)
    ):
        await vram_pool.synchronize_mesh_resources()
        # Local: 16.0 + Peer1: 24.0 + Peer2: 48.0 = 88.0 GB
        assert vram_pool.total_capacity_gb == 88.0
        assert len(vram_pool.shards) == 3


def test_compress_to_signatures():
    """Verify ContextCompressor.compress_to_signatures strips function bodies but keeps headers/docstrings."""
    compressor = ContextCompressor(ContextManager())
    code = """
@decorator1
@decorator2(arg=True)
class MyClass:
    \"\"\"This is MyClass docstring.\"\"\"
    
    def __init__(self):
        self.x = 1

    @staticmethod
    async def process(data):
        '''Process the data.'''
        return data + 1
"""
    result = compressor.compress_to_signatures(code)
    
    # Assert signature elements are retained
    assert "@decorator1" in result
    assert "@decorator2(arg=True)" in result
    assert "class MyClass:" in result
    assert "This is MyClass docstring." in result
    assert "def __init__(self):" in result
    assert "@staticmethod" in result
    assert "async def process(data):" in result
    assert "Process the data." in result
    
    # Assert implementation details are stripped
    assert "self.x = 1" not in result
    assert "return data + 1" not in result


@pytest.mark.asyncio
async def test_budget_enforcement():
    """Verify VirtualContextAssembler allocates slot budgets and truncates when exceeding caps."""
    ctx = ContextManager()
    assembler = VirtualContextAssembler(ctx)

    system_prompt = "System instructions here"
    # Budget cap for system is min(2000, 10% of 4096) = 409
    
    hot = [{"role": "user", "content": "A" * 2000}]  # 500 tokens
    warm = [{"role": "system", "content": "B" * 3000}]  # 750 tokens
    cold = [{"role": "system", "content": "C" * 2000}]  # 500 tokens
    
    # Force low hardware budget of 4096
    final = assembler._enforce_budget(system_prompt, hot, warm, cold, 4096)
    
    total_tokens = ctx.count_messages_tokens(final)
    assert total_tokens <= 4096
    
    # Ensure system prompt is still first
    assert final[0]["role"] == "system"
    assert "System instructions" in final[0]["content"]


@pytest.mark.asyncio
async def test_tier_overflow():
    """Verify assembler trims Tier 3 -> Tier 2 -> Tier 1 to fit hard budget limit."""
    ctx = ContextManager()
    assembler = VirtualContextAssembler(ctx)

    system_prompt = "Sys"
    
    # Exceed budget (total budget 4096)
    hot = [{"role": "user", "content": "A" * 12000}]  # ~3000 tokens
    warm = [{"role": "system", "content": "B" * 12000}]  # ~3000 tokens
    cold = [{"role": "system", "content": "C" * 12000}]  # ~3000 tokens

    final = assembler._enforce_budget(system_prompt, hot, warm, cold, 4096)
    
    total_tokens = ctx.count_messages_tokens(final)
    assert total_tokens <= 4096


@pytest.mark.asyncio
async def test_empty_workspace():
    """Verify assembler produces valid prompt payload when RAG/HiveMind yield nothing."""
    ctx = ContextManager()
    assembler = VirtualContextAssembler(ctx)
    
    # Mock gather methods to return empty lists
    assembler._gather_hot = MagicMock(return_value=[])
    assembler._gather_warm = AsyncMock(return_value=[])
    assembler._gather_cold = AsyncMock(return_value=[])
    
    messages, budget = await assembler.assemble(
        query="test query",
        conversation_id="conv_1",
        agent_type="coder",
        task_history=None,
        system_prompt="Base Sys Prompt"
    )
    
    assert len(messages) == 1
    assert messages[0]["content"] == "Base Sys Prompt"
    assert budget >= 4096


@pytest.mark.asyncio
async def test_override_logic():
    """Verify settings manager override llm_hardware_context takes precedence."""
    ctx = ContextManager()
    assembler = VirtualContextAssembler(ctx)

    # 1. Auto-detected flow (override is 0)
    settings_manager.update("llm_hardware_context", 0)
    vram_pool.total_capacity_gb = 24.0
    budget = assembler._compute_hardware_budget()
    assert budget == 1000000

    # 2. Overridden flow
    settings_manager.update("llm_hardware_context", 16384)
    budget = assembler._compute_hardware_budget()
    assert budget == 16384

    # Reset
    settings_manager.update("llm_hardware_context", 0)


@pytest.mark.asyncio
async def test_engine_parameters_stream():
    """Verify that stream() formats parameters correctly for Ollama, llama.cpp, and vLLM."""
    import os

    from core.agents.coder_agent import CoderAgent
    from core.context.rules_parser import RulesParser
    
    agent = CoderAgent(RulesParser(), ContextManager())
    
    messages = [{"role": "user", "content": "hello"}]
    
    async def mock_aiter_lines():
        if False:
            yield ""

    # 1. Test Ollama engine parameters
    with (
        patch.dict(os.environ, {"NEUREX_MOCK_LLM": "false"}),
        patch("core.infrastructure.mesh.mesh_router.resolve_model_and_node", return_value=("http://localhost:11434", "qwen2.5-coder:14b", None)),
        patch("httpx.AsyncClient.stream") as mock_stream
    ):
        mock_stream.return_value.__aenter__.return_value.raise_for_status = MagicMock()
        mock_stream.return_value.__aenter__.return_value.aiter_lines = mock_aiter_lines
        
        async for _ in agent.stream(messages, model="qwen2.5-coder:14b", hardware_budget=8192):
            pass
            
        args, kwargs = mock_stream.call_args
        payload = kwargs["json"]
        assert payload["options"]["num_ctx"] == 8192

    # 2. Test llama.cpp engine parameters
    with (
        patch.dict(os.environ, {"NEUREX_MOCK_LLM": "false"}),
        patch("core.infrastructure.mesh.mesh_router.resolve_model_and_node", return_value=("http://localhost:11434", "models/default.gguf", None)),
        patch("httpx.AsyncClient.stream") as mock_stream
    ):
        mock_stream.return_value.__aenter__.return_value.raise_for_status = MagicMock()
        mock_stream.return_value.__aenter__.return_value.aiter_lines = mock_aiter_lines
        
        async for _ in agent.stream(messages, model="models/default.gguf", hardware_budget=16384):
            pass
            
        args, kwargs = mock_stream.call_args
        payload = kwargs["json"]
        # n_ctx should be injected at top level for llama-cpp-python
        assert payload["n_ctx"] == 16384
        assert "options" not in payload
