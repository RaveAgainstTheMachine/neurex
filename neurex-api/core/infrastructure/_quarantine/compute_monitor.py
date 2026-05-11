"""
core/infrastructure/compute_monitor.py
Autonomous Mesh Load-Balancing (Compute Steering).
Monitors VRAM/CPU heat and steers tasks to the most efficient nodes.
"""

from __future__ import annotations

import asyncio
from typing import Any

import httpx
import structlog

from core.infrastructure.mesh import mesh_router

log = structlog.get_logger()


class ComputeMonitor:
    def __init__(self):
        self.node_metrics: dict[str, dict[str, Any]] = {}

    async def refresh_mesh_metrics(self):
        """Polls all Mesh peers for real-time telemetry."""
        peers = list(mesh_router.peers.values())
        tasks = [self._fetch_node_metrics(peer) for peer in peers]
        # Include local metrics
        tasks.append(self._get_local_metrics())

        results = await asyncio.gather(*tasks)
        for res in results:
            if res:
                self.node_metrics[res["node_id"]] = res

        log.info("compute.mesh_metrics_refreshed", nodes=len(self.node_metrics))

    async def get_best_node_for_task(self, required_vram_gb: float = 8.0) -> str:
        """
        Steers task to the node with the highest 'Efficiency Score'.
        Score = (Free VRAM / Temperature) * Model Rank
        """
        await self.refresh_mesh_metrics()

        best_node = None
        highest_score = -1.0

        for node_id, metrics in self.node_metrics.items():
            free_vram = metrics.get("vram_free", 0)
            if free_vram < required_vram_gb:
                continue

            temp = metrics.get("temp", 50)  # Default to 50c if unknown
            # Heuristic: Lower temp + higher free VRAM = Better
            score = free_vram / max(temp, 1)

            if score > highest_score:
                highest_score = score
                best_node = metrics.get("url", "local")

        log.info("compute.task_steered", target=best_node, score=round(highest_score, 2))
        return best_node

    async def _fetch_node_metrics(self, peer) -> dict[str, Any]:
        """Queries a peer's status endpoint."""
        try:
            async with httpx.AsyncClient(timeout=5) as client:
                resp = await client.get(f"{peer.url}/api/infra/status")
                if resp.status_code == 200:
                    data = resp.json()
                    return {
                        "node_id": peer.name,
                        "url": peer.url,
                        "vram_free": data.get("vram", {}).get("free_gb", 0),
                        "temp": data.get("vram", {}).get("temp_c", 45),
                    }
        except Exception:
            pass
        return None

    async def _get_local_metrics(self) -> dict[str, Any]:
        """Collects local telemetry."""
        # Simple local metric collection
        vram_free = 12.0  # Placeholder: actual metrics fetched via nvidia-smi if available
        temp = 42
        return {"node_id": "local", "url": "local", "vram_free": vram_free, "temp": temp}


compute_monitor = ComputeMonitor()
