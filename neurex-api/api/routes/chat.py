"""
api/routes/chat.py
REST endpoints for conversation history.
The primary interaction path is WebSocket (/ws/{id}), but these endpoints
let the frontend hydrate history on reconnect and fetch past conversations.
"""

from __future__ import annotations

import uuid
from datetime import UTC, datetime

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlmodel import Field, SQLModel, func, select
from sqlmodel.ext.asyncio.session import AsyncSession

from core.task_graph import engine, get_session

router = APIRouter()


# ── Models ────────────────────────────────────────────────────────────────────


class ChatMessage(SQLModel, table=True):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()), primary_key=True)
    conversation_id: str = Field(index=True)
    role: str  # "user" | "assistant"
    content: str
    graph_id: str | None = None  # links to the TaskGraph that produced this reply
    workspace_path: str | None = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))


class SendMessageRequest(BaseModel):
    conversation_id: str
    role: str
    content: str
    graph_id: str | None = None
    workspace_path: str | None = None


# ── Ensure table exists ────────────────────────────────────────────────────────


async def _init_chat_table():
    async with engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.create_all)


# ── Title helpers ─────────────────────────────────────────────────────────────


def _make_title(content: str, max_len: int = 60) -> str:
    """Derive a short title from the first line of a message."""
    title = content.strip().split("\n")[0]
    # Strip common prefixes (markdown, @mentions)
    for prefix in ("@[", "#", ">", "-", "*"):
        if title.startswith(prefix):
            title = title.lstrip("@[#>-* \t")
    if len(title) > max_len:
        title = title[: max_len - 3] + "..."
    return title or "Untitled"


# ── Routes ────────────────────────────────────────────────────────────────────


@router.get("/conversations")
async def list_conversations(
    workspace_path: str | None = None,
    session: AsyncSession = Depends(get_session)
):
    """Return distinct conversation IDs with last-message timestamps and smart titles."""
    if workspace_path:
        stmt = (
            select(ChatMessage.conversation_id, func.max(ChatMessage.created_at))
            .where(ChatMessage.workspace_path == workspace_path)
            .group_by(ChatMessage.conversation_id)
            .order_by(func.max(ChatMessage.created_at).desc())
        )
    else:
        stmt = (
            select(ChatMessage.conversation_id, func.max(ChatMessage.created_at))
            .group_by(ChatMessage.conversation_id)
            .order_by(func.max(ChatMessage.created_at).desc())
        )
    result = await session.exec(stmt)
    convs = [{"conversation_id": row[0], "last_message": row[1]} for row in result.all()]

    for conv in convs:
        cid = conv["conversation_id"]
        first_user = await session.exec(
            select(ChatMessage)
            .where(ChatMessage.conversation_id == cid, ChatMessage.role == "user")
            .order_by(ChatMessage.created_at)
            .limit(1)
        )
        msg = first_user.first()
        if msg and msg.content:
            conv["title"] = _make_title(msg.content)
        else:
            conv["title"] = cid[:8] + "…"

    return convs


@router.get("/{conversation_id}")
async def get_history(
    conversation_id: str,
    limit: int = 100,
    session: AsyncSession = Depends(get_session),
):
    """Return message history for a conversation, newest-last."""
    result = await session.exec(
        select(ChatMessage)
        .where(ChatMessage.conversation_id == conversation_id)
        .order_by(ChatMessage.created_at)
        .limit(limit)
    )
    return result.all()


@router.post("/message")
async def persist_message(
    req: SendMessageRequest,
    session: AsyncSession = Depends(get_session),
):
    """
    Persist a chat message. Called by the WS handler after each exchange
    so history survives reconnects.
    """
    msg = ChatMessage(
        conversation_id=req.conversation_id,
        role=req.role,
        content=req.content,
        graph_id=req.graph_id,
        workspace_path=req.workspace_path,
    )
    session.add(msg)
    await session.commit()
    await session.refresh(msg)
    return msg


@router.delete("/{conversation_id}")
async def clear_conversation(
    conversation_id: str,
    session: AsyncSession = Depends(get_session),
):
    """Clear all messages for a conversation."""
    result = await session.exec(
        select(ChatMessage).where(ChatMessage.conversation_id == conversation_id)
    )
    for msg in result.all():
        await session.delete(msg)
    await session.commit()
    # Also clear the shared scratchpad for this conversation
    from core.context.scratchpad import clear_scratchpad

    await clear_scratchpad(conversation_id)

    return {"deleted": True, "conversation_id": conversation_id}
