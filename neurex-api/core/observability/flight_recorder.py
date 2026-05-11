"""
core/observability/flight_recorder.py
Flight recorder for agentic decision-making. Stores structured 'Reasoning Traces'.
"""

import uuid
from datetime import datetime

import structlog
from sqlmodel import Field, SQLModel, select
from sqlmodel.ext.asyncio.session import AsyncSession

from core.task_graph import UTC, async_session, engine

log = structlog.get_logger()


class DecisionEvent(SQLModel, table=True):
    __table_args__ = {"extend_existing": True}
    id: str = Field(default_factory=lambda: str(uuid.uuid4()), primary_key=True)
    conversation_id: str = Field(index=True)
    task_id: str | None = Field(index=True, default=None)
    agent_type: str
    decision: str
    rationale: str
    context_keys: str | None = None  # JSON string of keys used in decision
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))


async def _init_recorder_table():
    async with engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.create_all)


import asyncio

log = structlog.get_logger()

# Phase 44.9: High-Throughput Decision Buffering
_DECISION_BUFFER: list[DecisionEvent] = []
_BUFFER_LOCK = asyncio.Lock()


async def record_decision(
    conversation_id: str,
    agent_type: str,
    decision: str,
    rationale: str,
    task_id: str | None = None,
    context_keys: list | None = None,
):
    """Log a decision to the buffer. Flushed automatically by background worker."""
    import json

    event = DecisionEvent(
        conversation_id=conversation_id,
        task_id=task_id,
        agent_type=agent_type,
        decision=decision,
        rationale=rationale,
        context_keys=json.dumps(context_keys) if context_keys else None,
    )

    async with _BUFFER_LOCK:
        _DECISION_BUFFER.append(event)

    log.debug("observability.decision_buffered", agent=agent_type, decision=decision)


async def flush_decisions():
    """Background worker to flush decisions in batches."""
    while True:
        await asyncio.sleep(2.0)

        async with _BUFFER_LOCK:
            if not _DECISION_BUFFER:
                continue
            to_flush = list(_DECISION_BUFFER)
            _DECISION_BUFFER.clear()

        try:
            async with async_session() as session:
                for event in to_flush:
                    session.add(event)
                await session.commit()
                log.info("observability.batch_flushed", count=len(to_flush))
        except Exception as e:
            log.error("observability.flush_failed", error=str(e))
            # Put them back? (Caveman says: just log error for now to keep it simple)


async def get_flight_log(conversation_id: str, limit: int = 50) -> list[dict]:
    """Retrieve the reasoning trace, including pending buffer items."""
    # 1. Fetch from DB
    async with async_session() as session:
        statement = (
            select(DecisionEvent)
            .where(DecisionEvent.conversation_id == conversation_id)
            .order_by(DecisionEvent.created_at.desc())
            .limit(limit)
        )

        result = await session.exec(statement)
        db_results = [r.dict() for r in result.all()]

    # 2. Add pending from buffer
    async with _BUFFER_LOCK:
        pending = [r.dict() for r in _DECISION_BUFFER if r.conversation_id == conversation_id]

    return (pending + db_results)[:limit]
