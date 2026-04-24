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
import os
import structlog
from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from fastapi import status as http_status

from core.orchestrator import Orchestrator
from core.context.manager import ContextManager
from core.context.rules_parser import RulesParser
from core.task_graph import AsyncSession

log = structlog.get_logger()
router = APIRouter()

API_TOKEN = os.getenv("API_TOKEN", "neurex-dev-token")


async def _authenticate(websocket: WebSocket) -> bool:
    token = websocket.query_params.get("token", "")
    if token != API_TOKEN:
        await websocket.close(code=http_status.WS_1008_POLICY_VIOLATION)
        return False
    return True


async def _persist_message(session: AsyncSession, conversation_id: str, role: str, content: str, graph_id: str | None = None):
    """Persist a chat message to SQLite so history survives reconnects."""
    from api.routes.chat import ChatMessage
    msg = ChatMessage(
        conversation_id=conversation_id,
        role=role,
        content=content,
        graph_id=graph_id,
    )
    session.add(msg)
    await session.commit()


@router.websocket("/ws/{conversation_id}")
async def websocket_endpoint(
    websocket: WebSocket,
    conversation_id: str,
):
    await websocket.accept()

    if not await _authenticate(websocket):
        return

    log.info("ws.connected", conversation_id=conversation_id)

    from core.task_graph import engine
    async with AsyncSession(engine) as session:
        rules = RulesParser()
        ctx = ContextManager()
        orch = Orchestrator(session, rules, ctx)

        try:
            while True:
                raw = await websocket.receive_text()
                msg = json.loads(raw)
                log.info("ws.message_received", type=msg.get("type"), conversation_id=conversation_id)

                if msg.get("type") == "cancel":
                    await websocket.send_json({"event": "cancelled"})
                    break

                if msg.get("type") == "message":
                    content = msg.get("content", "").strip()
                    if not content:
                        continue

                    # Persist the user message
                    await _persist_message(session, conversation_id, "user", content)

                    # Stream orchestrator events back over WS
                    assistant_tokens = []
                    last_graph_id = None
                    async for event in orch.run(content, conversation_id):
                        await websocket.send_json(event)
                        await asyncio.sleep(0)

                        # Collect assistant tokens for persistence
                        if event.get("event") == "token":
                            assistant_tokens.append(event["data"])
                        if event.get("event") in ("plan_ready", "done"):
                            last_graph_id = event.get("data", {}).get("graph_id")

                    # Persist the assistant reply
                    if assistant_tokens:
                        await _persist_message(
                            session, conversation_id, "assistant",
                            "".join(assistant_tokens), last_graph_id
                        )

                if msg.get("type") == "approve_plan":
                    graph_id = msg.get("graph_id")
                    if not graph_id:
                        continue

                    assistant_tokens = []
                    async for event in orch.resume(graph_id, conversation_id):
                        await websocket.send_json(event)
                        await asyncio.sleep(0)
                        if event.get("event") == "token":
                            assistant_tokens.append(event["data"])

                    if assistant_tokens:
                        await _persist_message(
                            session, conversation_id, "assistant",
                            "".join(assistant_tokens), graph_id
                        )

                if msg.get("type") == "approve_shell":
                    task_id = msg.get("task_id")
                    approved = msg.get("approved", False)
                    if not task_id:
                        continue

                    async for event in orch.resume_shell(task_id, approved, conversation_id):
                        await websocket.send_json(event)
                        await asyncio.sleep(0)

        except WebSocketDisconnect:
            log.info("ws.disconnected", conversation_id=conversation_id)
        except Exception as e:
            log.error("ws.error", error=str(e))
            try:
                await websocket.send_json({"event": "error", "data": str(e)})
                await websocket.close()
            except Exception:
                pass
