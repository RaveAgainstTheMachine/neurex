"""
tests/test_plugin_hub.py
Tests for the Extensible Plugin Hub routes (GET /marketplace, POST /publish).
"""

from __future__ import annotations

import pytest


@pytest.fixture(autouse=True)
def override_auth():
    from api.routes.auth import get_current_user
    from core.task_graph import User, UserRole
    from main import app

    mock_user = User(username="test_dev", role=UserRole.DEVELOPER)

    async def mock_get_current_user():
        return mock_user

    app.dependency_overrides[get_current_user] = mock_get_current_user
    yield
    app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_plugin_hub_marketplace_lifecycle(test_client):
    """
    Test the Plugin Hub lifecycle: querying marketplace, publishing a plugin,
    handling duplicates, and ensuring integration with the skills system.
    """
    from core.skills.manager import skill_manager

    mock_path = skill_manager.SKILLS_DIR / ".marketplace_mock.json"

    # Clean up mock file before starting
    if mock_path.exists():
        mock_path.unlink()

    try:
        # 1. Fetch initial marketplace catalog
        response = await test_client.get("/api/skills/marketplace")
        assert response.status_code == 200
        curated_list = response.json()
        assert len(curated_list) > 0
        assert any(c["id"] == "web-search" for c in curated_list)

        # 2. Publish a custom plugin
        payload = {
            "name": "Swarm Monitor",
            "description": "Visual swarm activity and thread latency metrics tracker.",
            "url": "https://github.com/neurex-swarm/skill-swarm-monitor",
            "author": "Mesh Devs",
            "version": "1.0.0",
            "category": "Core",
        }

        # Developer role is required for publishing
        response = await test_client.post("/api/skills/publish", json=payload)
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"
        assert data["skill"]["name"] == "Swarm Monitor"
        assert data["skill"]["id"] == "swarm-monitor"
        assert data["skill"]["category"] == "Core"

        # 3. Test publishing conflict on duplicate URL
        response = await test_client.post("/api/skills/publish", json=payload)
        assert response.status_code == 409
        assert "already published" in response.json()["detail"]

        # 4. Fetch the marketplace catalog again and verify the published plugin is included
        response = await test_client.get("/api/skills/marketplace")
        assert response.status_code == 200
        catalog = response.json()
        assert len(catalog) == len(curated_list) + 1
        published_item = [x for x in catalog if x["id"] == "swarm-monitor"][0]
        assert published_item["author"] == "Mesh Devs"
        assert published_item["version"] == "1.0.0"

    finally:
        # Clean up mock file at the end
        if mock_path.exists():
            mock_path.unlink()
