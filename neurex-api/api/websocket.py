"""
api/websocket.py
WebSocket endpoint. Each connection maps to one conversation.
Streams Orchestrator events as newline-delimited JSON.
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

        # Use the PTY manager from app state (initialized in main.py)
        pty_manager = websocket.app.state.pty_manager

        from core.collaboration.presence import presence_manager
        user_id = websocket.query_params.get("user_id", "Anonymous")
        await presence_manager.connect(conversation_id, websocket, user_id)

        # Define output callback for this conversation's terminal
        async def on_terminal_output(data: str):
            try:
                await websocket.send_json({"event": "terminal_output", "data": data})
            except:
                pass

        # Start/Get PTY session
        pty_session = pty_manager.create_session(
            conversation_id, 
            lambda data: asyncio.create_task(on_terminal_output(data))
        )

        try:
            while True:
                raw = await websocket.receive_text()
                msg = json.loads(raw)
                msg_type = msg.get("type")
                log.info("ws.message_received", type=msg_type, conversation_id=conversation_id)

                if msg_type == "presence_update":
                    await presence_manager.update_presence(conversation_id, user_id, msg.get("data", {}))
                    continue

                if msg_type == "cancel":
                    await websocket.send_json({"event": "cancelled"})
                    break

                if msg_type == "terminal_input":
                    pty_session.write(msg.get("data", ""))
                    continue

                if msg_type == "terminal_resize":
                    pty_session.resize(msg.get("rows", 24), msg.get("cols", 80))
                    continue

                if msg_type == "message":
                    content = msg.get("content", "").strip()
                    requested_model = msg.get("model")
                    if not content:
                        continue

                    await _persist_message(session, conversation_id, "user", content)

                    assistant_tokens = []
                    last_graph_id = None
                    try:
                        async for event in orch.run(content, conversation_id, model=requested_model):
                            await websocket.send_json(event)
                            await asyncio.sleep(0)
                            if event.get("event") == "token":
                                assistant_tokens.append(event["data"])
                            if event.get("event") in ("plan_ready", "done"):
                                last_graph_id = event.get("data", {}).get("graph_id")
                    except Exception as e:
                        log.error("ws.orch_run_error", error=str(e))
                        await websocket.send_json({"event": "error", "data": str(e)})
                    finally:
                        if assistant_tokens:
                            await _persist_message(
                                session, conversation_id, "assistant",
                                "".join(assistant_tokens), last_graph_id
                            )

                if msg_type == "approve_plan":
                    graph_id = msg.get("graph_id")
                    if not graph_id:
                        continue

                    assistant_tokens = []
                    try:
                        async for event in orch.resume(graph_id, conversation_id):
                            await websocket.send_json(event)
                            await asyncio.sleep(0)
                            if event.get("event") == "token":
                                assistant_tokens.append(event["data"])
                    finally:
                        if assistant_tokens:
                            await _persist_message(
                                session, conversation_id, "assistant",
                                "".join(assistant_tokens), graph_id
                            )

                if msg_type == "approve_shell":
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
        finally:
            await presence_manager.disconnect(conversation_id, websocket, user_id)
            pty_session.close()
