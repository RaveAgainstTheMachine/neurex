from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from core.infrastructure.mesh import mesh_router
from core.infrastructure.registry import LLMRecommender
from core.mcp.tools.install_tool import install_and_route_model
from core.settings.manager import settings_manager


@pytest.mark.asyncio
@patch("core.infrastructure.manager.InfrastructureManager.get_installed_models")
async def test_mesh_router_resolve_model_and_node(mock_get_installed):
    # Mock local models
    mock_get_installed.return_value = [
        {"name": "qwen2.5-coder:14b"},
        {"name": "deepseek-r1:14b"},
    ]
    
    # Enable recommendations
    settings_manager.update("enable_model_recommendations", True)
    
    # 1. Exact match test
    url, resolved, warning = await mesh_router.resolve_model_and_node("qwen2.5-coder:14b", "Coding")
    assert resolved == "qwen2.5-coder:14b"
    
    # 2. Fallback test (32b -> 14b)
    url, resolved, warning = await mesh_router.resolve_model_and_node("qwen2.5-coder:32b", "Coding")
    assert resolved == "qwen2.5-coder:14b"

@pytest.mark.asyncio
@patch("aiohttp.ClientSession.get")
async def test_discover_best_in_class(mock_get):
    # Mock Hugging Face API response
    mock_response = MagicMock()
    mock_response.status = 200
    mock_response.json = AsyncMock(return_value=[
        {
            "id": "Qwen/Qwen2.5-Coder-32B-Instruct-GGUF",
            "downloads": 1000,
            "likes": 100,
            "trendingScore": 50.0,
            "createdAt": "2026-01-01T00:00:00Z",
            "tags": ["32B", "gguf"],
            "cardData": {
                "model-index": [
                    {
                        "results": [
                            {
                                "metrics": [
                                    {"value": 0.925} # HumanEval score
                                ]
                            }
                        ]
                    }
                ]
            }
        }
    ])
    
    mock_context = MagicMock()
    mock_context.__aenter__.return_value = mock_response
    mock_get.return_value = mock_context
    
    # Reset cache
    LLMRecommender._cache.clear()
    
    best = await LLMRecommender.discover_best_in_class("Coding", available_vram_gb=24.0)
    assert best is not None
    assert best["id"] == "Qwen/Qwen2.5-Coder-32B-Instruct-GGUF"
    assert best["params"] == "32.0B"

@pytest.mark.asyncio
@patch("core.infrastructure.manager.InfrastructureManager.pull_model")
async def test_install_and_route_model(mock_pull):
    mock_pull.return_value = True
    
    # Set default routes
    routes = {"Coding": "qwen2.5-coder:14b"}
    settings_manager.update("model_routes", routes)
    
    res = await install_and_route_model("qwen2.5-coder:32b", "Coding")
    assert "Successfully installed and routed" in res
    assert settings_manager.get("model_routes")["Coding"] == "qwen2.5-coder:32b"
