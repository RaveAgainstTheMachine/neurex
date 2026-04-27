"""
api/routes/chat.py
REST endpoints for conversation history.
The primary interaction path is WebSocket (/ws/{id}), but these endpoints
let the frontend hydrate history on reconnect and fetch past conversations.
"""
from __future__ import annotations
import uuid
from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlmodel import SQLModel, Field, select
from sqlmodel.ext.asyncio.session import AsyncSession

from core.task_graph import get_session, engine
from sqlmodel import text

router = APIRouter()


# ── Models ────────────────────────────────────────────────────────────────────

class ChatMessage(SQLModel, table=True):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()), primary_key=True)
    conversation_id: str = Field(index=True)
    role: str                    # "user" | "assistant"
    content: str
    graph_id: Optional[str] = None  # links to the TaskGraph that produced this reply
    created_at: datetime = Field(default_factory=datetime.utcnow)


class SendMessageRequest(BaseModel):
    conversation_id: str
    role: str
    content: str
    graph_id: Optional[str] = None


# ── Ensure table exists ────────────────────────────────────────────────────────

async def _init_chat_table():
    async with engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.create_all)


# ── Routes ────────────────────────────────────────────────────────────────────

@router.get("/conversations")
async def list_conversations(session: AsyncSession = Depends(get_session)):
    """Return distinct conversation IDs with their latest message timestamps."""
    result = await session.exec(
        text(
            "SELECT conversation_id, MAX(created_at) AS last_message "
            "FROM chatmessage GROUP BY conversation_id ORDER BY last_message DESC"
        )
    )
    return [{"conversation_id": row[0], "last_message": row[1]} for row in result]


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
