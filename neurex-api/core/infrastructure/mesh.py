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
        self.models = []
        self.latency_ms = 0

    def to_dict(self):
        return {
            "url": self.url,
            "token": self.token,
            "name": self.name,
            "status": self.status,
            "vram_gb": self.vram_gb,
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
                peer.vram_gb = data.get("vram_gb", 0)
                peer.latency_ms = int((time.time() - start) * 1000)
                # In the future, parse available models from the response
                self._save_peers()
                log.debug("mesh.peer_healthy", url=url, latency=peer.latency_ms)
        except Exception as e:
            peer.status = "offline"
            self._save_peers()
            log.warning("mesh.peer_offline", url=url, error=str(e))

    async def get_best_inference_node(self) -> str:
        """
        Returns the Ollama base URL to use.
        Prioritizes the local host unless a peer has significantly more VRAM.
        """
        local_base = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
        
        # Simple heuristic: find peer with status=online and max VRAM
        best_peer = None
        max_vram = 0.0
        
        for peer in self.peers.values():
            if peer.status == "online" and peer.vram_gb > max_vram:
                max_vram = peer.vram_gb
                best_peer = peer
                
        # If a remote peer has > 8GB more VRAM than local (assuming local is 8GB for now), use it
        # TODO: Get actual local VRAM dynamically
        if best_peer and best_peer.vram_gb > 16.0:
            log.info("mesh.routing_remote", peer=best_peer.name, vram=best_peer.vram_gb)
            # We assume the remote Neurex node exposes Ollama, or we proxy it.
            # For phase 10, we proxy via the Neurex API
            return f"{best_peer.url}/api/infra/ollama_proxy"
            
        return local_base

mesh_router = MeshRouter()
