"""
api/websocket.py
WebSocket endpoint. Each connection maps to one conversation.
Streams Orchestrator events as newline-delimited JSON.
"""

from __future__ import annotations

import asyncio
import json
import os

import structlog
from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from fastapi import status as http_status

from core.context.manager import ContextManager
from core.context.rules_parser import RulesParser
from core.orchestrator import Orchestrator
from core.task_graph import AsyncSession

log = structlog.get_logger()
router = APIRouter()

from jose import JWTError, jwt

from api.routes.auth import ALGORITHM, get_secret_key


async def _authenticate(websocket: WebSocket) -> bool:
    token = websocket.query_params.get("token", "").strip()
    if not token:
        await websocket.close(code=http_status.WS_1008_POLICY_VIOLATION)
        return False
    try:
        payload = jwt.decode(token, get_secret_key(), algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            await websocket.close(code=http_status.WS_1008_POLICY_VIOLATION)
            return False
        log.info("ws.auth_success", user=username)
        return True
    except JWTError:
        await websocket.close(code=http_status.WS_1008_POLICY_VIOLATION)
        return False
    except Exception as e:
        log.error("ws.auth_crash", error=str(e))
        await websocket.close(code=http_status.WS_1008_POLICY_VIOLATION)
        return False


async def _persist_message(
    conversation_id: str, role: str, content: str, graph_id: str | None = None
):
    """Persist a chat message to SQLite so history survives reconnects. Uses its own session for isolation."""
    from api.routes.chat import ChatMessage
    from core.task_graph import AsyncSession, engine

    try:
        async with AsyncSession(engine, expire_on_commit=False) as session:
            msg = ChatMessage(
                conversation_id=conversation_id,
                role=role,
                content=content,
                graph_id=graph_id,
            )
            session.add(msg)
            await session.commit()
            log.debug("ws.message_persisted", role=role, conversation_id=conversation_id)
    except Exception as e:
        log.error("ws.persist_failed", error=str(e))


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

    async with AsyncSession(engine, expire_on_commit=False) as session:
        rules = RulesParser()
        ctx = ContextManager()
        orch = Orchestrator(session, rules, ctx)

        # Use the PTY manager from app state (initialized in main.py)
        pty_manager = websocket.app.state.pty_manager

        from core.collaboration.presence import presence_manager

        user_id = websocket.query_params.get("user_id", "Anonymous")
        await presence_manager.connect(conversation_id, websocket, user_id)

        # Define output callback for terminals
        attached_sessions = set()

        async def on_terminal_output(sid: str, data: str):
            try:
                await websocket.send_json(
                    {"event": "terminal_output", "sessionId": sid, "data": data}
                )
            except Exception:
                pass

        def get_output_handler(sid: str):
            return lambda data: asyncio.create_task(on_terminal_output(sid, data))

        # Initial default session
        default_pty = pty_manager.get_or_create_session(
            conversation_id, get_output_handler(conversation_id)
        )
        attached_sessions.add(conversation_id)

        try:
            while True:
                raw = await websocket.receive_text()
                msg = json.loads(raw)
                msg_type = msg.get("type")
                requested_sid = msg.get("sessionId")
                pty_sid = requested_sid
                if not pty_sid or pty_sid == "default":
                    pty_sid = conversation_id

                if msg_type == "ping":
                    await presence_manager.ping(conversation_id, user_id)
                    continue

                if msg_type == "presence_update":
                    await presence_manager.update_presence(
                        conversation_id, user_id, msg.get("data", {})
                    )
                    continue

                if msg_type == "cancel":
                    await websocket.send_json({"event": "cancelled"})
                    break

                if msg_type == "terminal_input":
                    if requested_sid not in attached_sessions:
                        s = pty_manager.get_or_create_session(
                            pty_sid, get_output_handler(requested_sid)
                        )
                        attached_sessions.add(requested_sid)
                    else:
                        s = pty_manager.get_or_create_session(pty_sid)
                    s.write(msg.get("data", ""))
                    continue

                if msg_type == "terminal_resize":
                    if requested_sid not in attached_sessions:
                        s = pty_manager.get_or_create_session(
                            pty_sid, get_output_handler(requested_sid)
                        )
                        attached_sessions.add(requested_sid)
                    else:
                        s = pty_manager.get_or_create_session(pty_sid)
                    s.resize(msg.get("rows", 24), msg.get("cols", 80))
                    continue

                if msg_type == "terminal_sync":
                    cwd = msg.get("cwd")
                    s = pty_manager.get_or_create_session(
                        pty_sid, get_output_handler(requested_sid), cwd=cwd
                    )
                    if requested_sid not in attached_sessions:
                        attached_sessions.add(requested_sid)
                    if s.history:
                        await on_terminal_output(requested_sid, s.history)
                    continue

                if msg_type == "terminal_clear":
                    s = pty_manager.get_session(pty_sid)
                    if s:
                        s.clear()
                    continue

                if msg_type == "terminal_kill":
                    pty_manager.close_session(pty_sid)
                    if requested_sid in attached_sessions:
                        attached_sessions.remove(requested_sid)
                    continue

                if msg_type == "set_autonomy":
                    level = msg.get("level", "limited")
                    orch.set_autonomy_level(level)
                    log.info("ws.autonomy_updated", level=level, conversation_id=conversation_id)
                    continue

                if msg_type == "message":
                    content = msg.get("content", "").strip()
                    requested_model = msg.get("model")
                    if not content:
                        continue

                    await _persist_message(conversation_id, "user", content)

                    assistant_tokens = []
                    last_graph_id = None
                    try:
                        async for event in orch.run(
                            content, conversation_id, model=requested_model
                        ):
                            await websocket.send_json(event)
                            if event.get("event") == "token":
                                assistant_tokens.append(event["data"])
                            if event.get("event") in ("plan_ready", "done"):
                                last_graph_id = event.get("data", {}).get("graph_id")
                            await asyncio.sleep(0)
                    except Exception as e:
                        log.error("ws.orch_run_error", error=str(e))
                        await websocket.send_json({"event": "error", "data": str(e)})
                    finally:
                        # Persist assistant response if any tokens were produced,
                        # or if a graph was started (to link history to graph)
                        if assistant_tokens or last_graph_id:
                            text_content = (
                                "".join(assistant_tokens) if assistant_tokens else "Plan generated."
                            )
                            await _persist_message(
                                conversation_id, "assistant", text_content, last_graph_id
                            )

                if msg_type == "approve_plan":
                    graph_id = msg.get("graph_id")
                    if not graph_id:
                        continue

                    assistant_tokens = []
                    try:
                        async for event in orch.resume(graph_id, conversation_id):
                            await websocket.send_json(event)
                            if event.get("event") == "token":
                                assistant_tokens.append(event["data"])
                            await asyncio.sleep(0)
                    finally:
                        if assistant_tokens:
                            await _persist_message(
                                conversation_id, "assistant", "".join(assistant_tokens), graph_id
                            )

                if msg_type == "approve_shell":
                    task_id = msg.get("task_id")
                    approved = msg.get("approved", False)
                    if not task_id:
                        continue

                    async for event in orch.resume_shell(task_id, approved, conversation_id):
                        await websocket.send_json(event)
                        await asyncio.sleep(0)

                if msg_type == "inline_edit":
                    path = msg.get("path")
                    prompt = msg.get("prompt")
                    selection = msg.get("selection")
                    range_coords = msg.get("range")
                    task_id = msg.get("taskId")

                    if not (path and prompt and task_id):
                        continue

                    try:
                        async for event in orch.execute_inline_edit(
                            path, prompt, selection, range_coords, task_id, conversation_id
                        ):
                            await websocket.send_json(event)
                            await asyncio.sleep(0)
                    except Exception as e:
                        log.error("ws.inline_edit_error", error=str(e))
                        await websocket.send_json({"event": "error", "data": str(e)})

                if msg_type == "terminal_command_approval":
                    task_id = msg.get("taskId")
                    approved = msg.get("approved", False)
                    s = pty_manager.get_session(pty_sid)
                    if s and task_id:
                        fut = s.pending_approvals.get(task_id)
                        if fut and not fut.done():
                            fut.set_result(approved)
                            log.info("ws.terminal_command_approval", task_id=task_id, approved=approved, session_id=pty_sid)
                    continue

                if msg_type == "debate_steer":
                    verdict = msg.get("verdict", "").strip()
                    if verdict:
                        ctx.debate_verdicts[conversation_id] = verdict
                        log.info("ws.debate_steer", conversation_id=conversation_id, verdict=verdict)
                    continue

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
            for sid in attached_sessions:
                s = pty_manager.get_session(sid)
                if s:
                    s.detach(get_output_handler(sid))


@router.websocket("/ws/lsp/{lang}")
async def lsp_websocket_endpoint(websocket: WebSocket, lang: str):
    await websocket.accept()

    if not await _authenticate(websocket):
        return

    workspace_path = websocket.query_params.get("workspace", os.getcwd())
    lsp_manager = websocket.app.state.lsp_manager

    try:
        session = await lsp_manager.get_session(lang, workspace_path)
    except Exception as e:
        log.error("lsp.start_failed", lang=lang, error=str(e))
        await websocket.send_json({"event": "error", "data": str(e)})
        await websocket.close()
        return

    log.info("lsp.connected", lang=lang, workspace=workspace_path)

    async def forward_to_lsp():
        try:
            while True:
                data = await websocket.receive_bytes()
                await session.write(data)
        except WebSocketDisconnect:
            pass
        except Exception as e:
            log.error("lsp.forward_error", lang=lang, error=str(e))

    async def forward_to_ws():
        try:
            while True:
                data = await session.read_stdout()
                if not data:
                    break
                await websocket.send_bytes(data)
        except Exception as e:
            log.error("lsp.receive_error", lang=lang, error=str(e))

    try:
        await asyncio.gather(forward_to_lsp(), forward_to_ws())
    except Exception as e:
        log.error("lsp.bridge_crash", lang=lang, error=str(e))
    finally:
        # We don't stop the session here because multiple tabs might use the same language LSP
        # But for the prototype, we just log it
        log.info("lsp.disconnected", lang=lang)
