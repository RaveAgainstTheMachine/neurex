"""
core/infrastructure/mesh.py
Manages the decentralized Neurex Mesh Federation.
Handles peer discovery, health checks, and LLM load balancing across nodes.
"""
import os
import json
import asyncio
import httpx
import structlog
from pathlib import Path
from typing import List, Dict, Any

log = structlog.get_logger()

PEERS_FILE = Path(os.getenv("WORKSPACE_PATH", "/workspace")) / ".neurex" / "mesh_peers.json"

class PeerNode:
    def __init__(self, url: str, token: str, name: str = "Unknown"):
        self.url = url.rstrip("/")
        self.token = token
        self.name = name
        self.status = "offline"
        self.vram_gb = 0.0
        self.ram_total_gb = 0.0
        self.cpu_percent = 0.0
        self.models = []
        self.latency_ms = 0

    def to_dict(self):
        return {
            "url": self.url,
            "token": self.token,
            "name": self.name,
            "status": self.status,
            "vram_gb": self.vram_gb,
            "ram_total_gb": self.ram_total_gb,
            "cpu_percent": self.cpu_percent,
            "models": self.models,
            "latency_ms": self.latency_ms
        }

class MeshRouter:
    def __init__(self):
        self.peers: Dict[str, PeerNode] = {}
        self._load_peers()

    def _load_peers(self):
        PEERS_FILE.parent.mkdir(parents=True, exist_ok=True)
        if PEERS_FILE.exists():
            try:
                with open(PEERS_FILE, "r") as f:
                    data = json.load(f)
                    for peer_data in data:
                        peer = PeerNode(peer_data["url"], peer_data.get("token", ""))
                        peer.name = peer_data.get("name", "Unknown")
                        self.peers[peer.url] = peer
            except Exception as e:
                log.error("mesh.load_failed", error=str(e))

    def _save_peers(self):
        with open(PEERS_FILE, "w") as f:
            json.dump([p.to_dict() for p in self.peers.values()], f, indent=2)

    def add_peer(self, url: str, token: str, name: str) -> bool:
        url = url.rstrip("/")
        if url in self.peers:
            return False
        self.peers[url] = PeerNode(url, token, name)
        self._save_peers()
        asyncio.create_task(self.check_health(url))
        return True

    def remove_peer(self, url: str):
        if url in self.peers:
            del self.peers[url]
            self._save_peers()

    async def check_health(self, url: str):
        """Ping a peer to update its status and capabilities."""
        peer = self.peers.get(url)
        if not peer: return

        import time
        start = time.time()
        try:
            async with httpx.AsyncClient(timeout=5) as client:
                resp = await client.get(f"{peer.url}/api/infra/status", headers={"Authorization": f"Bearer {peer.token}"})
                resp.raise_for_status()
                data = resp.json()
                
                peer.status = "online"
                metrics = data.get("metrics", {})
                peer.vram_gb = metrics.get("vram_gb", 0.0)
                peer.ram_total_gb = metrics.get("ram_total_gb", 0.0)
                peer.cpu_percent = metrics.get("cpu_percent", 0.0)
                peer.models = data.get("local_models", [])
                peer.queue_depth = data.get("queue_depth", 0)
                peer.latency_ms = int((time.time() - start) * 1000)
                self._save_peers()
                log.debug("mesh.peer_healthy", url=url, latency=peer.latency_ms)
        except Exception as e:
            peer.status = "offline"
            self._save_peers()
            log.warning("mesh.peer_offline", url=url, error=str(e))

    async def get_best_inference_node(self, model_name: str | None = None) -> str:
        """
        Returns the Ollama base URL to use.
        Uses a Weighted-Load algorithm to calculate node capability scores.
        If model_name is provided, filters for nodes that already have the model.
        """
        from core.infrastructure.manager import infrastructure_manager
        local_metrics = infrastructure_manager.get_system_metrics()
        local_vram = local_metrics.get("vram_gb", 8.0)
        local_cpu = local_metrics.get("cpu_percent", 0.0)
        
        # 1. Start with local node
        local_models = await infrastructure_manager.get_installed_models("ollama")
        has_model_locally = not model_name or any(model_name in m for m in local_models)
        
        # Boost local score if it has the model; penalize if it doesn't
        local_multiplier = 2.0 if has_model_locally else 0.1
        best_score = (local_vram * local_multiplier) / (local_cpu + 1)
        best_url = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
        
        for peer in self.peers.values():
            if peer.status != "online":
                continue
            
            # 2. Check if peer has the model
            has_model_on_peer = not model_name or any(model_name in m for m in peer.models)
            peer_multiplier = 2.0 if has_model_on_peer else 0.1
            
            # 3. Peer Score calculation
            load_factor = peer.cpu_percent + (peer.latency_ms / 10) + (getattr(peer, 'queue_depth', 0) * 20)
            score = (peer.vram_gb * peer_multiplier) / (load_factor + 1)
            
            if score > best_score:
                best_score = score
                best_url = f"{peer.url}/api/infra/ollama_proxy"
                
        log.info("mesh.routing_decided", target=best_url, model=model_name, score=round(best_score, 2))
        return best_url

    async def start_monitoring(self, interval_seconds: int = 60):
        """Background task to periodically refresh peer health and telemetry."""
        log.info("mesh.monitor_started", interval=interval_seconds)
        while True:
            tasks = [self.check_health(url) for url in self.peers.keys()]
            if tasks:
                await asyncio.gather(*tasks)
            await asyncio.sleep(interval_seconds)

mesh_router = MeshRouter()
