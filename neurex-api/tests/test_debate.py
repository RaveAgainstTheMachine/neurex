"""
tests/test_debate.py
Tests for Multi-Agent Consensus Debates route and sequencer.
"""

from __future__ import annotations

from unittest.mock import AsyncMock, patch

import pytest
from sqlmodel import select

from core.task_graph import DebateSession


@pytest.mark.asyncio
async def test_debate_endpoints(test_client, db_session):
    """
    Test POST /api/debate/start and GET /api/debate/status.
    """
    # 1. Trigger the start route
    conv_id = "test-debate-conv"
    query = "Should we use PostgreSQL or SQLite?"

    # We mock run_debate_sequencer to avoid triggering the actual background execution during endpoint test
    with patch("api.routes.debate.run_debate_sequencer", new_callable=AsyncMock) as mock_sequencer:
        response = await test_client.post(
            "/api/debate/start", json={"conversation_id": conv_id, "query": query}
        )
        assert response.status_code == 200
        assert response.json() == {"status": "ok", "message": "Debate sequence initialized."}
        mock_sequencer.assert_called_once_with(conv_id, query)

    # 2. Add sample debate messages directly to the database
    from datetime import UTC, datetime

    m1 = DebateSession(
        id="msg-1",
        conversation_id=conv_id,
        agent_role="planner",
        content="I plan to use SQLite.",
        timestamp=datetime.now(UTC),
    )
    m2 = DebateSession(
        id="msg-2",
        conversation_id=conv_id,
        agent_role="coder",
        content="Coding SQLite is easy.",
        timestamp=datetime.now(UTC),
    )
    db_session.add(m1)
    db_session.add(m2)
    await db_session.commit()

    # 3. Test the GET /api/debate/status endpoint
    response = await test_client.get(f"/api/debate/status?conversation_id={conv_id}")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 2
    assert data[0]["role"] == "planner"
    assert data[0]["agent"] == "Planner Agent"
    assert data[0]["content"] == "I plan to use SQLite."
    assert data[1]["role"] == "coder"
    assert data[1]["agent"] == "Coder Agent"
    assert data[1]["content"] == "Coding SQLite is easy."


@pytest.mark.asyncio
async def test_debate_sequencer(db_session):
    """
    Test that the sequencer runs Planner, Coder, Reviewer, and Judge,
    broadcasting events and persisting them to the database.
    """
    conv_id = "test-seq-conv"
    query = "How to refactor core orchestrator?"

    # Mock the websocket presence_manager broadcast
    with (
        patch(
            "core.collaboration.presence.presence_manager.broadcast", new_callable=AsyncMock
        ) as mock_broadcast,
        patch("core.agents.debater_agent.DebaterAgent.stream") as mock_stream,
    ):
        # We need mock_stream to yield tokens and then a done event for each round
        async def mock_generator(*args, **kwargs):
            yield {"type": "token", "text": "Tradeoffs "}
            yield {"type": "token", "text": "considered."}
            yield {"type": "done"}

        mock_stream.side_effect = mock_generator

        from api.routes.debate import run_debate_sequencer

        await run_debate_sequencer(conv_id, query)

        # The sequencer must have broadcast events for all 4 rounds:
        assert mock_broadcast.call_count >= 4

        # Verify database records
        result = await db_session.exec(
            select(DebateSession)
            .where(DebateSession.conversation_id == conv_id)
            .order_by(DebateSession.timestamp)
        )
        records = result.all()
        assert len(records) == 4

        # Verify the sequential roles
        assert records[0].agent_role == "planner"
        assert records[1].agent_role == "coder"
        assert records[2].agent_role == "reviewer"
        assert records[3].agent_role == "judge"

        for r in records:
            assert r.content == "Tradeoffs considered."
            if r.agent_role == "judge":
                assert r.verdict == "Tradeoffs considered."
