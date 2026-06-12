"""
api/routes/events.py
Endpoint for external triggers (git hooks, CI/CD, test runners) to start Neurex background tasks.
"""

import os

import structlog
from fastapi import APIRouter, Depends, Header, HTTPException
from pydantic import BaseModel

log = structlog.get_logger()

router = APIRouter()

class EventPayload(BaseModel):
    trigger: str
    payload: dict
    conversation_id: str = "background"

async def verify_secret(authorization: str = Header(None)):
    secret = os.getenv("NEUREX_EVENTS_SECRET")
    if not secret:
        # If no secret is configured, endpoint is disabled for security
        raise HTTPException(status_code=503, detail="Events endpoint is disabled (NEUREX_EVENTS_SECRET not set).")
    
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Missing or invalid Authorization header.")
    
    token = authorization.split("Bearer ")[1]
    if token != secret:
        raise HTTPException(status_code=401, detail="Invalid NEUREX_EVENTS_SECRET.")

@router.post("")
async def trigger_event(event: EventPayload, _=Depends(verify_secret)):
    """
    Triggers an agentic run based on an external event.
    The orchestrator handles the planning and execution.
    """
    log.info("events.trigger_received", trigger=event.trigger, conversation_id=event.conversation_id)
    
    # Map triggers to natural language requests for the orchestrator
    request_text = f"An external event '{event.trigger}' occurred."
    if event.trigger == "test_failed":
        request_text += " Please investigate the failing tests and fix them."
    elif event.trigger == "git_push":
        request_text += " Please review the recent commits and ensure documentation is updated."
    else:
        request_text += f" Payload: {event.payload}"

    import asyncio

    from core.context.manager import ContextManager
    from core.context.rules_parser import RulesParser
    from core.orchestrator import Orchestrator
    from core.task_graph import AsyncSession, engine

    async def run_orchestrator(req_text: str, conv_id: str):
        async with AsyncSession(engine, expire_on_commit=False) as session:
            rules = RulesParser()
            ctx = ContextManager()
            orch = Orchestrator(session, rules, ctx)
            async for _ in orch.run(req_text, conv_id):
                pass

    # Fire and forget
    asyncio.create_task(run_orchestrator(request_text, event.conversation_id))
    
    return {"status": "accepted", "trigger": event.trigger, "message": "Event queued for background processing."}
