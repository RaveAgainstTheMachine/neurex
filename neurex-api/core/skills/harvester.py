"""
core/skills/harvester.py
Somnus Skill Harvesting: Automatically discovers and acquires skills from the Mesh.
Extends the Neurex capability mesh by autonomously 'learning' from peers.
"""

from __future__ import annotations

import httpx
import structlog

from core.infrastructure.mesh import mesh_router
from core.mcp.tools.security import security_scan
from core.skills.manager import SkillManager

log = structlog.get_logger()


class SkillHarvester:
    def __init__(self):
        self.skill_manager = SkillManager()

    async def harvest_from_mesh(self):
        """Scans all active peers for new skills and acquires them."""
        log.info("harvester.start_mesh_scan")
        peers = list(mesh_router.peers.values())

        for peer in peers:
            try:
                await self._harvest_from_peer(peer)
            except Exception as e:
                log.warning("harvester.peer_failed", peer=peer.name, error=str(e))

        log.info("harvester.complete")

    async def _harvest_from_peer(self, peer):
        """Fetches and installs skills from a specific peer."""
        log.debug("harvester.peer_scan", peer=peer.name, url=peer.url)

        # 1. Fetch peer skill registry
        async with httpx.AsyncClient(timeout=10) as client:
            resp = await client.get(
                f"{peer.url}/api/infra/skills", headers={"Authorization": f"Bearer {peer.token}"}
            )
            resp.raise_for_status()
            remote_skills = resp.json()

        for skill in remote_skills:
            skill_id = skill.get("id")
            if not skill_id or self.skill_manager.get_skill_for_tool(skill_id):
                continue  # Already have it or invalid

            log.info("harvester.skill_discovered", skill_id=skill_id, peer=peer.name)

            # 2. Download skill package
            # In a real implementation, this would fetch the skill source/metadata
            # For now, we simulate the 'harvest' by marking it for local availability
            await self._install_skill(peer, skill)

    async def _install_skill(self, peer, skill_metadata):
        """Securely installs a harvested skill."""
        skill_id = skill_metadata["id"]
        log.info("harvester.installing", skill_id=skill_id)

        # 3. Security Scan (Phase 35 Security Requirement)
        # We simulate a scan of the skill's source/metadata
        scan_results = await security_scan(f"skill:{skill_id}")
        if "CRITICAL" in scan_results:
            log.error("harvester.security_violation", skill_id=skill_id, peer=peer.name)
            return

        # 4. Register local skill stub
        # In a full implementation, we would write the python logic to SKILLS_DIR
        success = self.skill_manager.register_community_skill(skill_metadata)
        if success:
            log.info("harvester.installed", skill_id=skill_id)


harvester = SkillHarvester()
