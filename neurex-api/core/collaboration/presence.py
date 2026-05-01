"""
core/collaboration/presence.py
Manages real-time user presence and cursor broadcasting.
"""
import asyncio
import time
import structlog
from typing import Dict, List, Set, Any
from fastapi import WebSocket

log = structlog.get_logger()

class PresenceManager:
    def __init__(self):
        # Map conversation_id -> Set of active WebSockets
        self.active_connections: Dict[str, Set[WebSocket]] = {}
        # Map conversation_id -> user_id -> presence_data
        self.presence_state: Dict[str, Dict[str, Any]] = {}
        self.node_id = "node-" + str(time.time()) # Unique ID for this specific instance
        self._tasks: List[asyncio.Task] = []

    def start(self):
        """Starts background tasks once an event loop is running."""
        if not self._tasks:
            self._tasks.append(asyncio.create_task(self._sweep_zombies()))
            self._tasks.append(asyncio.create_task(self._heartbeat_system()))

    async def _heartbeat_system(self):
        """Periodically broadcasts this node's compute capabilities to the mesh."""
        from core.infrastructure.distributed import distributed_manager
        while True:
            await asyncio.sleep(15) # Pulse every 15 seconds
            caps = distributed_manager.get_status()
            
            # Update local state and broadcast to all conversations
            for conv_id in list(self.active_connections.keys()):
                await self.update_presence(conv_id, self.node_id, {
                    "type": "compute_node",
                    "capabilities": caps
                })

    async def connect(self, conversation_id: str, websocket: WebSocket, user_id: str):
        if conversation_id not in self.active_connections:
            self.active_connections[conversation_id] = set()
            self.presence_state[conversation_id] = {}
        
        self.active_connections[conversation_id].add(websocket)
        self.presence_state[conversation_id][user_id] = {
            "user_id": user_id,
            "cursor": None,
            "active_file": None,
            "status": "online",
            "last_ping": time.time()
        }
        await self.broadcast(conversation_id, {
            "event": "presence_update",
            "data": list(self.presence_state[conversation_id].values())
        })

    async def disconnect(self, conversation_id: str, websocket: WebSocket, user_id: str):
        if conversation_id in self.active_connections:
            self.active_connections[conversation_id].discard(websocket)
            if user_id in self.presence_state[conversation_id]:
                del self.presence_state[conversation_id][user_id]
            
            await self.broadcast(conversation_id, {
                "event": "presence_update",
                "data": list(self.presence_state[conversation_id].values())
            })

    async def update_presence(self, conversation_id: str, user_id: str, data: Dict[str, Any]):
        if conversation_id in self.presence_state and user_id in self.presence_state[conversation_id]:
            self.presence_state[conversation_id][user_id].update(data)
            self.presence_state[conversation_id][user_id]["last_ping"] = time.time()
            await self.broadcast(conversation_id, {
                "event": "presence_update",
                "data": list(self.presence_state[conversation_id].values())
            }, exclude_user=user_id)

    async def ping(self, conversation_id: str, user_id: str):
        if conversation_id in self.presence_state and user_id in self.presence_state[conversation_id]:
            self.presence_state[conversation_id][user_id]["last_ping"] = time.time()

    async def _sweep_zombies(self):
        """Continuously clean up connections that haven't pinged in 25 seconds."""
        while True:
            await asyncio.sleep(10) # More frequent sweeps
            now = time.time()
            for conv_id, users in list(self.presence_state.items()):
                # If no ping for 25s, they are likely gone (frontend pings every 15s)
                zombies = [uid for uid, data in users.items() if now - data.get("last_ping", now) > 25]
                if zombies:
                    for z in zombies:
                        del self.presence_state[conv_id][z]
                        log.info("ws.zombie_swept", user_id=z, conversation_id=conv_id)
                    
                    # Update all remaining participants
                    await self.broadcast(conv_id, {
                        "event": "presence_update",
                        "data": list(self.presence_state[conv_id].values())
                    })

    async def broadcast(self, conversation_id: str, message: Any, exclude_user: str = None):
        """Phase 44.14: Parallel Multi-Socket Broadcasting."""
        if conversation_id not in self.active_connections:
            return

        connections = list(self.active_connections[conversation_id])
        if not connections:
            return

        async def safe_send(ws: WebSocket):
            try:
                await ws.send_json(message)
                return None
            except Exception:
                return ws

        # Parallel dispatch to all clients in the conversation
        results = await asyncio.gather(*[safe_send(ws) for ws in connections])
        
        # Cleanup dead connections
        for ws in [r for r in results if r is not None]:
            self.active_connections[conversation_id].discard(ws)

    async def broadcast_global(self, message: Any):
        """Parallel dispatch across all active conversations."""
        conv_ids = list(self.active_connections.keys())
        if conv_ids:
            await asyncio.gather(*[self.broadcast(cid, message) for cid in conv_ids])

presence_manager = PresenceManager()
