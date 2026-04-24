"""
api/websocket.py
WebSocket endpoint. Each connection maps to one conversation.
Streams Orchestrator events as newline-delimited JSON.

Message shapes from server:
  {"event": "task_created",  "data": {TaskNode}}
  {"event": "task_updated",  "data": {"id": ..., "status": ...}}
  {"event": "token",         "data": "string token"}
  {"event": "done",          "data": {"graph_id": ..., "tasks": [...]}}
  {"event": "error",         "data": "message"}

Message shapes from client:
  {"type": "message", "content": "user text"}
  {"type": "cancel"}
"""
from __future__ import annotations
import json
import asyncio
import structlog
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends, Header
from fastapi import status as http_status

from core.orchestrator import Orchestrator
from core.context.manager import ContextManager
from core.context.rules_parser import RulesParser
from core.task_graph import get_session, AsyncSession

log = structlog.get_logger()
router = APIRouter()

import os
API_TOKEN = os.getenv("API_TOKEN", "neurex-dev-token")


async def _authenticate(websocket: WebSocket) -> bool:
    token = websocket.query_params.get("token", "")
    if token != API_TOKEN:
        await websocket.close(code=http_status.WS_1008_POLICY_VIOLATION)
        return False
    return True


@router.websocket("/ws/{conversation_id}")
async def websocket_endpoint(
    websocket: WebSocket,
    conversation_id: str,
):
    await websocket.accept()

    if not await _authenticate(websocket):
        return

    log.info("ws.connected", conversation_id=conversation_id)

    async with AsyncSession(engine) as session:  # noqa: F821 — imported in main
        rules    = RulesParser()
        ctx      = ContextManager()
        orch     = Orchestrator(session, rules, ctx)

        try:
            while True:
                raw = await websocket.receive_text()
                msg = json.loads(raw)

                if msg.get("type") == "cancel":
                    await websocket.send_json({"event": "cancelled"})
                    break

                if msg.get("type") == "message":
                    content = msg.get("content", "").strip()
                    if not content:
                        continue

                    # Stream orchestrator events back over WS
                    async for event in orch.run(content, conversation_id):
                        await websocket.send_json(event)
                        await asyncio.sleep(0)


                if msg.get("type") == "approve_plan":
                    graph_id = msg.get("graph_id")
                    if not graph_id:
                        continue
                    
                    async for event in orch.resume(graph_id, conversation_id):
                        await websocket.send_json(event)
                        await asyncio.sleep(0)


        except WebSocketDisconnect:
            log.info("ws.disconnected", conversation_id=conversation_id)
        except Exception as e:
            log.error("ws.error", error=str(e))
            await websocket.send_json({"event": "error", "data": str(e)})
            await websocket.close()


# Late import to avoid circular dependency
from sqlalchemy.ext.asyncio import create_async_engine
from core.task_graph import DATABASE_URL
engine = create_async_engine(DATABASE_URL)
