"""
api/routes/debate.py
Endpoints and background task sequencer for Multi-Agent Consensus Debates.
"""

from __future__ import annotations

import asyncio
import uuid
from datetime import UTC, datetime

import structlog
from fastapi import APIRouter, BackgroundTasks, Depends
from pydantic import BaseModel
from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession

from core.agents.debater_agent import DebaterAgent
from core.collaboration.presence import presence_manager
from core.context.manager import ContextManager
from core.context.rules_parser import RulesParser
from core.task_graph import DebateSession, engine, get_session

log = structlog.get_logger()
router = APIRouter()


class DebateStartRequest(BaseModel):
    conversation_id: str
    query: str


async def run_debate_sequencer(conversation_id: str, query: str):
    """
    Executes the round-robin debate between Planner, Coder, and Reviewer agents,
    followed by the Architect Judge final verdict.
    """
    log.info("debate.sequencer.start", conversation_id=conversation_id, query=query)

    rules = RulesParser()
    ctx = ContextManager()
    debater = DebaterAgent(rules, ctx)

    # We will run 4 rounds: planner, coder, reviewer, and finally the judge.
    rounds = [
        {"role": "planner", "name": "Planner Agent", "persona": "optimist"},
        {"role": "coder", "name": "Coder Agent", "persona": "skeptic"},
        {"role": "reviewer", "name": "Reviewer Agent", "persona": "reviewer"},
        {"role": "judge", "name": "Architect Judge", "persona": "judge"},
    ]

    prior_arguments: list[tuple[str, str]] = []

    for rnd in rounds:
        role = rnd["role"]
        agent_name = rnd["name"]
        persona = rnd["persona"]

        message_id = str(uuid.uuid4())
        timestamp_str = datetime.now(UTC).strftime("%H:%M:%S")

        # Broadcast initial empty message
        await presence_manager.broadcast(
            conversation_id,
            {
                "event": "debate_message",
                "data": {
                    "id": message_id,
                    "agent": agent_name,
                    "role": role,
                    "content": "",
                    "timestamp": timestamp_str,
                },
            },
        )

        # Assemble task description with prior transcript
        transcript_str = ""
        if prior_arguments:
            transcript_str = "\n\nHere is the technical debate transcript so far:\n"
            for r_name, r_content in prior_arguments:
                transcript_str += f"- [{r_name}]: {r_content}\n"

        if role == "judge":
            task_desc = (
                f"Analyze the following architectural debate and render a final, definitive verdict. "
                f"Address key concerns raised by the Coder and Reviewer, and support the final decision.\n\n"
                f"Proposed query: {query}\n{transcript_str}"
            )
        else:
            task_desc = (
                f'Analyze and critique the following proposed technical plan/query:\n"{query}"\n'
                f"Participate in the debate, addressing prior arguments where relevant.\n{transcript_str}"
            )

        task = {"description": task_desc, "persona": persona}

        accumulated_content = ""
        try:
            async for chunk in debater.execute(task, conversation_id):
                if chunk.get("type") == "token":
                    token = chunk.get("text", "")
                    accumulated_content += token
                    await presence_manager.broadcast(
                        conversation_id,
                        {
                            "event": "debate_message",
                            "data": {
                                "id": message_id,
                                "agent": agent_name,
                                "role": role,
                                "content": accumulated_content,
                                "timestamp": timestamp_str,
                            },
                        },
                    )
                    # Yield CPU for smooth concurrency
                    await asyncio.sleep(0.01)
        except Exception as e:
            log.error("debate.round_error", role=role, error=str(e))
            accumulated_content = f"Error generating critique: {str(e)}"
            await presence_manager.broadcast(
                conversation_id,
                {
                    "event": "debate_message",
                    "data": {
                        "id": message_id,
                        "agent": agent_name,
                        "role": role,
                        "content": accumulated_content,
                        "timestamp": timestamp_str,
                    },
                },
            )

        # Add to local transcript for the next round
        prior_arguments.append((agent_name, accumulated_content))

        # Persist the round to database
        try:
            async with AsyncSession(engine, expire_on_commit=False) as session:
                session_record = DebateSession(
                    id=message_id,
                    conversation_id=conversation_id,
                    agent_role=role,
                    content=accumulated_content,
                    timestamp=datetime.now(UTC),
                    verdict=accumulated_content if role == "judge" else None,
                )
                session.add(session_record)
                await session.commit()
        except Exception as db_err:
            log.error("debate.persist_failed", role=role, error=str(db_err))

    log.info("debate.sequencer.done", conversation_id=conversation_id)


@router.post("/start")
async def start_debate(req: DebateStartRequest, background_tasks: BackgroundTasks):
    """
    Start a multi-agent technical debate for the given query.
    Executes in the background and broadcasts events via WebSockets.
    """
    # Clear old debate sessions for this conversation to prevent mixing
    try:
        async with AsyncSession(engine, expire_on_commit=False) as session:
            result = await session.exec(
                select(DebateSession).where(DebateSession.conversation_id == req.conversation_id)
            )
            records = result.all()
            for r in records:
                await session.delete(r)
            await session.commit()
    except Exception as db_err:
        log.error("debate.clear_previous_failed", error=str(db_err))

    background_tasks.add_task(run_debate_sequencer, req.conversation_id, req.query)
    return {"status": "ok", "message": "Debate sequence initialized."}


@router.get("/status")
async def get_debate_status(conversation_id: str, session: AsyncSession = Depends(get_session)):
    """
    Get the debate messages/transcript for the given conversation_id.
    """
    result = await session.exec(
        select(DebateSession)
        .where(DebateSession.conversation_id == conversation_id)
        .order_by(DebateSession.timestamp)
    )
    records = result.all()

    mapped = []
    for r in records:
        role = r.agent_role
        agent_name = "Planner Agent"
        if role == "coder":
            agent_name = "Coder Agent"
        elif role == "reviewer":
            agent_name = "Reviewer Agent"
        elif role == "judge":
            agent_name = "Architect Judge"

        mapped.append(
            {
                "id": r.id,
                "agent": agent_name,
                "role": role,
                "content": r.content,
                "timestamp": r.timestamp.strftime("%H:%M:%S"),
            }
        )
    return mapped
