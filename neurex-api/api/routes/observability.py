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
