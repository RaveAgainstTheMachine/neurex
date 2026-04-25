"""
core/collaboration/presence.py
Manages real-time user presence and cursor broadcasting.
"""
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

    async def connect(self, conversation_id: str, websocket: WebSocket, user_id: str):
        if conversation_id not in self.active_connections:
            self.active_connections[conversation_id] = set()
            self.presence_state[conversation_id] = {}
        
        self.active_connections[conversation_id].add(websocket)
        self.presence_state[conversation_id][user_id] = {
            "user_id": user_id,
            "cursor": None,
            "active_file": None,
            "status": "online"
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
        if conversation_id in self.presence_state:
            self.presence_state[conversation_id][user_id].update(data)
            await self.broadcast(conversation_id, {
                "event": "presence_update",
                "data": list(self.presence_state[conversation_id].values())
            }, exclude_user=user_id)

    async def broadcast(self, conversation_id: str, message: Any, exclude_user: str = None):
        """Send a message to all connected clients in a conversation."""
        if conversation_id not in self.active_connections:
            return

        dead_connections = set()
        for ws in self.active_connections[conversation_id]:
            try:
                await ws.send_json(message)
            except Exception:
                dead_connections.add(ws)

        for dead in dead_connections:
            self.active_connections[conversation_id].discard(dead)

presence_manager = PresenceManager()
