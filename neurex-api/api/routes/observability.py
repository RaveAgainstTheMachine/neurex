"""
api/routes/observability.py
Observability endpoints for the Flight Recorder.
"""

from fastapi import APIRouter, HTTPException

from core.observability.flight_recorder import get_flight_log

router = APIRouter()


@router.get("/trace/{conversation_id}")
async def fetch_flight_trace(conversation_id: str):
    """Retrieve the reasoning trace for a specific conversation."""
    try:
        return await get_flight_log(conversation_id)
    except Exception as e:
        import structlog

        log = structlog.get_logger()
        log.error(
            "observability.fetch_failed",
            conversation_id=conversation_id,
            error=str(e),
            exc_info=True,
        )
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/replay/{conversation_id}")
async def get_teleplay_replay(conversation_id: str):
    """Retrieve and format decision logs as chronological screenplay beats."""
    import json
    from datetime import datetime

    import structlog
    from sqlmodel import select

    from core.observability.flight_recorder import _BUFFER_LOCK, _DECISION_BUFFER, DecisionEvent
    from core.task_graph import async_session

    log = structlog.get_logger()
    try:
        # 1. Fetch all events for the conversation from the DB
        async with async_session() as session:
            statement = (
                select(DecisionEvent)
                .where(DecisionEvent.conversation_id == conversation_id)
                .order_by(DecisionEvent.created_at.asc())
            )
            result = await session.exec(statement)
            db_results = [r.model_dump() for r in result.all()]

        # 2. Add pending items from buffer
        async with _BUFFER_LOCK:
            pending = [
                r.model_dump() for r in _DECISION_BUFFER if r.conversation_id == conversation_id
            ]

        # Combine all events
        all_events = db_results + pending
        # Sort by created_at ascending
        all_events.sort(key=lambda x: x.get("created_at") or datetime.min)

        # 3. Format into screenplay beats
        beats = []
        for idx, event in enumerate(all_events, start=1):
            context_metadata = {}
            if event.get("context_keys"):
                try:
                    context_metadata = json.loads(event["context_keys"])
                except Exception:
                    pass

            timestamp_str = ""
            if event.get("created_at"):
                if isinstance(event["created_at"], str):
                    timestamp_str = event["created_at"]
                else:
                    timestamp_str = event["created_at"].isoformat()

            beats.append(
                {
                    "beat_number": idx,
                    "timestamp": timestamp_str,
                    "agent_type": event.get("agent_type"),
                    "act": event.get("decision"),
                    "narrative": event.get("rationale"),
                    "context_metadata": context_metadata,
                }
            )
        return beats
    except Exception as e:
        log.error(
            "observability.replay_failed",
            conversation_id=conversation_id,
            error=str(e),
            exc_info=True,
        )
        raise HTTPException(status_code=500, detail=str(e))
