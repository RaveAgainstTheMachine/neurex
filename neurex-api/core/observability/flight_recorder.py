"""
core/observability/flight_recorder.py
Flight recorder for agentic decision-making. Stores structured 'Reasoning Traces'.
"""
import uuid
from datetime import datetime
from typing import Optional
from sqlmodel import SQLModel, Field, select
from sqlmodel.ext.asyncio.session import AsyncSession
from core.task_graph import get_session, engine
import structlog

log = structlog.get_logger()

class DecisionEvent(SQLModel, table=True):
    __table_args__ = {"extend_existing": True}
    id: str = Field(default_factory=lambda: str(uuid.uuid4()), primary_key=True)
    conversation_id: str = Field(index=True)
    task_id: Optional[str] = Field(index=True, default=None)
    agent_type: str
    decision: str
    rationale: str
    context_keys: Optional[str] = None # JSON string of keys used in decision
    created_at: datetime = Field(default_factory=datetime.utcnow)

async def _init_recorder_table():
    async with engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.create_all)

async def record_decision(
    conversation_id: str,
    agent_type: str,
    decision: str,
    rationale: str,
    task_id: Optional[str] = None,
    context_keys: Optional[list] = None
):
    """Log a structured decision to the flight recorder."""
    import json
    async with AsyncSession(engine) as session:
        event = DecisionEvent(
            conversation_id=conversation_id,
            task_id=task_id,
            agent_type=agent_type,
            decision=decision,
            rationale=rationale,
            context_keys=json.dumps(context_keys) if context_keys else None
        )
        session.add(event)
        await session.commit()
        log.info("observability.decision_recorded", agent=agent_type, decision=decision)

async def get_flight_log(conversation_id: str, limit: int = 50) -> list[dict]:
    """Retrieve the reasoning trace for a conversation."""
    async with AsyncSession(engine) as session:
        statement = select(DecisionEvent).where(
            DecisionEvent.conversation_id == conversation_id
        ).order_by(DecisionEvent.created_at.desc()).limit(limit)
        
        result = await session.exec(statement)
        return [r.dict() for r in result.all()]
