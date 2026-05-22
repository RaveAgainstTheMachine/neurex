"""
tests/test_graph_mutation.py
Tests for task graph mutation endpoints and breakpoint checks.
"""

from __future__ import annotations

import pytest

from core.task_graph import TaskNode, TaskStatus, create_task


@pytest.mark.asyncio
async def test_toggle_breakpoint_endpoint(test_client, db_session):
    """POST /api/tasks/{task_id}/toggle_breakpoint must toggle is_checkpoint."""
    node = await create_task(
        db_session,
        graph_id="graph-break",
        agent_type="coder",
        title="Break Task",
        description="Will toggle",
    )
    assert not node.is_checkpoint

    # Toggle true
    res = await test_client.post(f"/api/tasks/{node.id}/toggle_breakpoint")
    assert res.status_code == 200
    data = res.json()
    assert data["is_checkpoint"] is True

    # Toggle false
    res = await test_client.post(f"/api/tasks/{node.id}/toggle_breakpoint")
    assert res.status_code == 200
    data = res.json()
    assert data["is_checkpoint"] is False


@pytest.mark.asyncio
async def test_approve_single_task_endpoint(test_client, db_session):
    """POST /api/tasks/{task_id}/approve must bypass breakpoint and set status to PENDING."""
    node = await create_task(
        db_session,
        graph_id="graph-approve",
        agent_type="coder",
        title="Approve Task",
        description="Will approve",
        is_checkpoint=True,
    )
    assert node.is_checkpoint

    res = await test_client.post(f"/api/tasks/{node.id}/approve")
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "pending"

    # Reload from database to verify checkpoint cleared and status pending
    await db_session.close()  # Reset local session cache
    from sqlmodel.ext.asyncio.session import AsyncSession

    from core.task_graph import engine
    async with AsyncSession(engine) as session:
        refreshed = await session.get(TaskNode, node.id)
        assert refreshed.status == TaskStatus.PENDING
        assert not refreshed.is_checkpoint


@pytest.mark.asyncio
async def test_mutate_graph_rewire(test_client, db_session):
    """POST /api/tasks/{graph_id}/mutate rewire action must update parent_id."""
    graph_id = "graph-mutate-1"
    t1 = await create_task(
        db_session, graph_id=graph_id, agent_type="planner", title="T1", description="Node 1"
    )
    t2 = await create_task(
        db_session, graph_id=graph_id, agent_type="coder", title="T2", description="Node 2"
    )
    assert t2.parent_id is None

    payload = {
        "action": "rewire",
        "task_id": t2.id,
        "parent_id": t1.id
    }
    res = await test_client.post(f"/api/tasks/{graph_id}/mutate", json=payload)
    assert res.status_code == 200
    data = res.json()
    assert data["mutated"] is True
    assert data["task"]["parent_id"] == t1.id


@pytest.mark.asyncio
async def test_mutate_graph_insert(test_client, db_session):
    """POST /api/tasks/{graph_id}/mutate insert action must create a new node and rewire optionally."""
    graph_id = "graph-mutate-2"
    t1 = await create_task(
        db_session, graph_id=graph_id, agent_type="planner", title="Root", description="Root node"
    )
    t2 = await create_task(
        db_session, graph_id=graph_id, agent_type="coder", title="Leaf", description="Leaf node", parent_id=t1.id
    )

    # Insert a new node between t1 and t2
    payload = {
        "action": "insert",
        "parent_id": t1.id,
        "child_id": t2.id,
        "title": "Middle",
        "description": "Intermediate node",
        "agent_type": "coder"
    }
    res = await test_client.post(f"/api/tasks/{graph_id}/mutate", json=payload)
    assert res.status_code == 200
    data = res.json()
    assert data["mutated"] is True
    new_node_id = data["task"]["id"]
    assert data["task"]["parent_id"] == t1.id

    # Verify child node is now rewired to the new middle node
    await db_session.close()
    from sqlmodel.ext.asyncio.session import AsyncSession

    from core.task_graph import engine
    async with AsyncSession(engine) as session:
        refreshed_t2 = await session.get(TaskNode, t2.id)
        assert refreshed_t2.parent_id == new_node_id


@pytest.mark.asyncio
async def test_mutate_graph_delete(test_client, db_session):
    """POST /api/tasks/{graph_id}/mutate delete action must delete node and rewire children."""
    graph_id = "graph-mutate-3"
    t1 = await create_task(
        db_session, graph_id=graph_id, agent_type="planner", title="T1", description="Node 1"
    )
    t2 = await create_task(
        db_session, graph_id=graph_id, agent_type="coder", title="T2", description="Node 2", parent_id=t1.id
    )
    t3 = await create_task(
        db_session, graph_id=graph_id, agent_type="reviewer", title="T3", description="Node 3", parent_id=t2.id
    )

    # Delete middle node t2
    payload = {
        "action": "delete",
        "task_id": t2.id
    }
    res = await test_client.post(f"/api/tasks/{graph_id}/mutate", json=payload)
    assert res.status_code == 200
    data = res.json()
    assert data["mutated"] is True

    # Verify t3 is rewired to t1
    await db_session.close()
    from sqlmodel.ext.asyncio.session import AsyncSession

    from core.task_graph import engine
    async with AsyncSession(engine) as session:
        refreshed_t3 = await session.get(TaskNode, t3.id)
        assert refreshed_t3.parent_id == t1.id
        
        # Verify t2 is gone
        deleted_node = await session.get(TaskNode, t2.id)
        assert deleted_node is None


@pytest.mark.asyncio
async def test_mutate_graph_modify(test_client, db_session):
    """POST /api/tasks/{graph_id}/mutate modify action must edit node title, description, and agent_type."""
    graph_id = "graph-mutate-4"
    t1 = await create_task(
        db_session, graph_id=graph_id, agent_type="planner", title="Original Title", description="Original Desc"
    )

    payload = {
        "action": "modify",
        "task_id": t1.id,
        "title": "Modified Title",
        "description": "Modified Desc",
        "agent_type": "coder"
    }
    res = await test_client.post(f"/api/tasks/{graph_id}/mutate", json=payload)
    assert res.status_code == 200
    data = res.json()
    assert data["mutated"] is True
    assert data["task"]["title"] == "Modified Title"
    assert data["task"]["description"] == "Modified Desc"
    assert data["task"]["agent_type"] == "coder"

    # Reload from database to verify persistence
    await db_session.close()
    from sqlmodel.ext.asyncio.session import AsyncSession

    from core.task_graph import engine
    async with AsyncSession(engine) as session:
        refreshed = await session.get(TaskNode, t1.id)
        assert refreshed.title == "Modified Title"
        assert refreshed.description == "Modified Desc"
        assert refreshed.agent_type == "coder"

