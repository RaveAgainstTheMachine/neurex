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

PEERS_FILE = Path.home() / ".neurex" / "mesh_peers.json"

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
        self.queue_depth = 0
        self.tps = 0.0
        self.rpc_endpoint = None
        self.distributed_status = {}
        # Predictive State
        self.history: List[Dict[str, Any]] = []
        self.predicted_load = 0.0

    def record_telemetry(self, metrics: Dict[str, Any]):
        """Append a metric snapshot and prune history."""
        import time
        snapshot = {
            "timestamp": time.time(),
            "cpu": metrics.get("cpu_percent", 0.0),
            "vram": metrics.get("vram_gb", 0.0),
            "queue": metrics.get("queue_depth", 0)
        }
        self.history.append(snapshot)
        # Keep last 1 hour of history (assuming 60s checks)
        if len(self.history) > 60:
            self.history.pop(0)

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
            "latency_ms": self.latency_ms,
            "queue_depth": self.queue_depth,
            "tps": self.tps,
            "rpc_endpoint": self.rpc_endpoint,
            "distributed": self.distributed_status,
            "predicted_load": self.predicted_load
        }

class ResourcePredictor:
    """Analyzes historical telemetry to predict upcoming resource bottlenecks."""
    
    @staticmethod
    def predict_future_load(history: List[Dict[str, Any]]) -> float:
        """
        Calculates a trend-aware load prediction score.
        Uses a weighted moving average of the last 5 snapshots.
        """
        if len(history) < 3:
            return 0.0
            
        recent = history[-5:]
        # Weights: more recent = more important
        weights = [0.1, 0.15, 0.2, 0.25, 0.3]
        weights = weights[-len(recent):] # adjust if < 5
        
        # Normalize weights
        total_w = sum(weights)
        norm_weights = [w/total_w for w in weights]
        
        prediction = 0.0
        for i, snap in enumerate(recent):
            # Combined load metric: CPU + (Queue * 10)
            load = snap["cpu"] + (snap["queue"] * 10)
            prediction += load * norm_weights[i]
            
        return round(prediction, 2)

class MeshRouter:
    def __init__(self):
        self.peers: Dict[str, PeerNode] = {}
        # Phase 44.10: Persistent Telemetry Client
        self._client: httpx.AsyncClient = httpx.AsyncClient(timeout=5)
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
        """Ping a peer to update its status via persistent client."""
        peer = self.peers.get(url)
        if not peer: return

        import time
        start = time.time()
        try:
            resp = await self._client.get(f"{peer.url}/api/infra/status", headers={"Authorization": f"Bearer {peer.token}"})
            resp.raise_for_status()
            data = resp.json()
                
            peer.status = "online"
            metrics = data.get("metrics", {})
            peer.vram_gb = metrics.get("vram_gb", 0.0)
            peer.ram_total_gb = metrics.get("ram_total_gb", 0.0)
            peer.cpu_percent = metrics.get("cpu_percent", 0.0)
            peer.models = data.get("local_models", [])
            peer.queue_depth = data.get("queue_depth", 0)
            peer.tps = metrics.get("benchmarks", {}).get("tps", 0.0)
            peer.latency_ms = int((time.time() - start) * 1000)
            
            # RPC Info
            dist = data.get("distributed", {})
            peer.rpc_endpoint = dist.get("rpc_endpoint")
            peer.distributed_status = dist

            # Update Predictive Analytics
            peer.record_telemetry(metrics)
            peer.predicted_load = ResourcePredictor.predict_future_load(peer.history)

            self._save_peers()
            log.debug("mesh.peer_healthy", url=url, latency=peer.latency_ms, predicted_load=peer.predicted_load)
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
        from core.infrastructure.benchmarker import benchmarker
        import random

        candidates = []

        # 1. Evaluate Local Node
        local_metrics = infrastructure_manager.get_system_metrics()
        local_vram = local_metrics.get("vram_gb", 8.0)
        local_cpu = local_metrics.get("cpu_percent", 0.0)
        local_models = await infrastructure_manager.get_installed_models("ollama")
        has_model_locally = not model_name or any(model_name in m for m in local_models)
        
        local_tps = benchmarker.last_results.get("tps", 0.0)
        local_tps_boost = 1 + (local_tps / 10.0)
        local_multiplier = 2.0 if has_model_locally else 0.1
        
        # Local node has 0 latency and usually 0 queue depth if we just started, 
        # but we should ideally track it. For now, assume 0 latency.
        local_load = (local_cpu / 2) + 0 # queue_depth not tracked locally yet
        local_score = (local_vram * local_multiplier * local_tps_boost) / (max(0.1, local_load))
        
        candidates.append({
            "url": os.getenv("OLLAMA_BASE_URL", "http://localhost:11434"),
            "score": local_score,
            "name": "Local Node"
        })

        # 2. Evaluate Peer Nodes
        for peer in self.peers.values():
            if peer.status != "online":
                continue
            
            has_model_on_peer = not model_name or any(model_name in m for m in peer.models)
            peer_multiplier = 2.0 if has_model_on_peer else 0.1
            tps_boost = 1 + (peer.tps / 10.0)
            
            # Penalize by latency, CPU load, current task queue, and PREDICTED load
            # queue_depth weight is high (25), predicted_load adds trend-awareness
            load_factor = (peer.cpu_percent / 2) + (peer.latency_ms / 20) + (peer.queue_depth * 25) + (peer.predicted_load * 0.5)
            score = (peer.vram_gb * peer_multiplier * tps_boost) / (max(0.1, load_factor))
            
            candidates.append({
                "url": f"{peer.url}/api/infra/ollama_proxy",
                "score": score,
                "name": peer.name
            })

        if not candidates:
            return os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")

        # 3. Selection Logic (Balanced)
        # Sort by score descending
        candidates.sort(key=lambda x: x["score"], reverse=True)
        
        # To prevent 'dogpiling', if the top few nodes have scores within 5% of each other,
        # pick randomly among them.
        best_score = candidates[0]["score"]
        top_tier = [c for c in candidates if c["score"] >= best_score * 0.95]
        
        selected = random.choice(top_tier)
        
        log.info("mesh.routing_decided", 
                 target=selected["url"], 
                 node=selected["name"],
                 model=model_name, 
                 score=round(selected["score"], 2),
                 tier_size=len(top_tier))
        
        return selected["url"]

    async def start_monitoring(self, interval_seconds: int = 60):
        """Background task to periodically refresh peer health and telemetry."""
        log.info("mesh.monitor_started", interval=interval_seconds)
        while True:
            tasks = [self.check_health(url) for url in self.peers.keys()]
            if tasks:
                await asyncio.gather(*tasks)
            
            # Phase 47: Sync Virtual VRAM Pool
            from core.infrastructure.vram_pool import vram_pool
            await vram_pool.synchronize_mesh_resources()
            
            await asyncio.sleep(interval_seconds)

mesh_router = MeshRouter()
