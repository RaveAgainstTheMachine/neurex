"""
tests/test_task_graph.py
Tests for the SQLite-backed task graph engine.
"""
from __future__ import annotations

import pytest
import pytest_asyncio
from sqlmodel import SQLModel
from sqlmodel.ext.asyncio.session import AsyncSession

from core.task_graph import (
    TaskNode,
    TaskStatus,
    create_task,
    get_graph,
    update_task,
    engine,
)


@pytest_asyncio.fixture
async def tg_session():
    """Isolated DB session for task graph tests."""
    async with engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.create_all)
    async with AsyncSession(engine, expire_on_commit=False) as session:
        yield session
    async with engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.drop_all)


@pytest.mark.asyncio
async def test_create_task_returns_node(tg_session):
    """Creating a task must return a TaskNode with correct fields."""
    node = await create_task(
        tg_session,
        graph_id="test-graph-1",
        agent_type="planner",
        title="Test Plan",
        description="Test the planning pipeline",
    )
    assert isinstance(node, TaskNode)
    assert node.graph_id == "test-graph-1"
    assert node.agent_type == "planner"
    assert node.title == "Test Plan"
    assert node.status == TaskStatus.PENDING


@pytest.mark.asyncio
async def test_update_task_status(tg_session):
    """Updating a task must change its status."""
    node = await create_task(
        tg_session,
        graph_id="test-graph-2",
        agent_type="coder",
        title="Write code",
        description="Implement feature",
    )
    await update_task(tg_session, node.id, TaskStatus.THINKING)
    
    refreshed = await tg_session.get(TaskNode, node.id)
    assert refreshed.status == TaskStatus.THINKING


@pytest.mark.asyncio
async def test_update_task_with_result(tg_session):
    """Completing a task must store its result string."""
    node = await create_task(
        tg_session,
        graph_id="test-graph-3",
        agent_type="coder",
        title="Write code",
        description="Implement feature",
    )
    await update_task(tg_session, node.id, TaskStatus.DONE, result="Created file.py")
    
    refreshed = await tg_session.get(TaskNode, node.id)
    assert refreshed.status == TaskStatus.DONE
    assert refreshed.result == "Created file.py"


@pytest.mark.asyncio
async def test_get_graph_returns_all_nodes(tg_session):
    """get_graph must return all nodes for a given graph_id."""
    graph_id = "test-graph-4"
    await create_task(tg_session, graph_id=graph_id, agent_type="planner", title="Plan", description="Plan it")
    await create_task(tg_session, graph_id=graph_id, agent_type="coder", title="Code", description="Code it")
    await create_task(tg_session, graph_id=graph_id, agent_type="reviewer", title="Review", description="Review it")
    
    graph = await get_graph(tg_session, graph_id)
    assert len(graph) == 3
    agent_types = {n.agent_type for n in graph}
    assert agent_types == {"planner", "coder", "reviewer"}


@pytest.mark.asyncio
async def test_get_graph_isolates_by_id(tg_session):
    """get_graph must NOT return nodes from a different graph."""
    await create_task(tg_session, graph_id="graph-A", agent_type="planner", title="A", description="Graph A")
    await create_task(tg_session, graph_id="graph-B", agent_type="coder", title="B", description="Graph B")
    
    graph_a = await get_graph(tg_session, "graph-A")
    assert len(graph_a) == 1
    assert graph_a[0].title == "A"


@pytest.mark.asyncio
async def test_task_failure_stores_error(tg_session):
    """Failing a task must store the error message."""
    node = await create_task(
        tg_session,
        graph_id="test-graph-5",
        agent_type="coder",
        title="Failing task",
        description="Will fail",
    )
    await update_task(tg_session, node.id, TaskStatus.FAILED, error="Connection refused")
    
    refreshed = await tg_session.get(TaskNode, node.id)
    assert refreshed.status == TaskStatus.FAILED
    assert "Connection refused" in (refreshed.error or "")


@pytest.mark.asyncio
async def test_parent_child_relationship(tg_session):
    """Tasks can have parent-child relationships."""
    parent = await create_task(
        tg_session,
        graph_id="test-graph-6",
        agent_type="planner",
        title="Parent",
        description="Plan",
    )
    child = await create_task(
        tg_session,
        graph_id="test-graph-6",
        parent_id=parent.id,
        agent_type="coder",
        title="Child",
        description="Code",
    )
    assert child.parent_id == parent.id
