from unittest.mock import AsyncMock, MagicMock, patch

import httpx
import pytest

from core.infrastructure.mesh import PeerNode
from core.skills.harvester import SkillHarvester


@pytest.mark.asyncio
async def test_skills_harvester_flow():
    harvester = SkillHarvester()
    harvester.skill_manager = MagicMock()
    # Mock skill_manager to not have the skill yet
    harvester.skill_manager.get_skill_for_tool.return_value = None
    harvester.skill_manager.register_community_skill.return_value = True

    peer = PeerNode("http://peer1", "token1", "PeerOne")
    peers = {"http://peer1": peer}

    mock_response = MagicMock(spec=httpx.Response)
    mock_response.status_code = 200
    mock_response.json.return_value = [
        {"id": "new-skill", "name": "New Skill"}
    ]

    with patch("core.infrastructure.mesh.mesh_router.peers", peers):
        with patch("httpx.AsyncClient.get", new_callable=AsyncMock, return_value=mock_response):
            with patch("core.skills.harvester.security_scan", new_callable=AsyncMock, return_value="SAFE") as mock_scan:
                await harvester.harvest_from_mesh()
                mock_scan.assert_called_once_with("skill:new-skill")
                harvester.skill_manager.register_community_skill.assert_called_once()

@pytest.mark.asyncio
async def test_skills_harvester_security_failure():
    harvester = SkillHarvester()
    harvester.skill_manager = MagicMock()
    harvester.skill_manager.get_skill_for_tool.return_value = None

    peer = PeerNode("http://peer1", "token1", "PeerOne")
    peers = {"http://peer1": peer}

    mock_response = MagicMock(spec=httpx.Response)
    mock_response.status_code = 200
    mock_response.json.return_value = [
        {"id": "malicious-skill", "name": "Malicious Skill"}
    ]

    with patch("core.infrastructure.mesh.mesh_router.peers", peers):
        with patch("httpx.AsyncClient.get", new_callable=AsyncMock, return_value=mock_response):
            with patch("core.skills.harvester.security_scan", new_callable=AsyncMock, return_value="CRITICAL VULNERABILITY") as mock_scan:
                await harvester.harvest_from_mesh()
                harvester.skill_manager.register_community_skill.assert_not_called()
