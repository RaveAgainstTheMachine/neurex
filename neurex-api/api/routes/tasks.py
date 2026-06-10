"""api/routes/tasks.py — Task graph REST endpoints."""

from fastapi import APIRouter, Depends
from pydantic import BaseModel

from core.task_graph import AsyncSession, TaskNode, TaskStatus, get_graph, get_session

router = APIRouter()


class GraphMutation(BaseModel):
    action: str  # "rewire", "insert", "delete"
    task_id: str | None = None
    parent_id: str | None = None
    child_id: str | None = None
    title: str | None = None
    description: str | None = None
    agent_type: str | None = None


@router.get("/", response_model=list[dict])
async def list_tasks(graph_id: str | None = None, session: AsyncSession = Depends(get_session)):
    from sqlmodel import select

    from api.routes.chat import ChatMessage

    query = select(TaskNode)
    if graph_id:
        # Check if this graph_id is a conversation ID by looking up associated ChatMessages
        graph_stmt = select(ChatMessage.graph_id).where(
            ChatMessage.conversation_id == graph_id, ChatMessage.graph_id.is_not(None)
        )
        graph_res = await session.exec(graph_stmt)
        graph_ids = list(set(graph_res.all()))

        if graph_ids:
            query = query.where(TaskNode.graph_id.in_(graph_ids))
        else:
            # Fallback to direct graph query
            query = query.where(TaskNode.graph_id == graph_id)

    result = await session.exec(query.order_by(TaskNode.created_at.desc()))
    return [n.model_dump() for n in result.all()]


@router.delete("/", response_model=dict)
async def delete_all_tasks(session: AsyncSession = Depends(get_session)):
    from sqlmodel import delete

    await session.exec(delete(TaskNode))
    await session.commit()
    return {"deleted": True}


@router.post("/{graph_id}/approve_all")
async def approve_all_tasks(graph_id: str, session: AsyncSession = Depends(get_session)):
    """Approve all PENDING or AWAITING_APPROVAL tasks in a graph."""
    from sqlmodel import select

    stmt = select(TaskNode).where(
        TaskNode.graph_id == graph_id,
        TaskNode.status.in_([TaskStatus.AWAITING_APPROVAL, TaskStatus.PENDING]),
    )
    result = await session.exec(stmt)
    tasks = result.all()

    for task in tasks:
        task.status = TaskStatus.PENDING
        session.add(task)

    await session.commit()
    return {"approved_count": len(tasks)}


@router.get("/{graph_id}/graph", response_model=list[dict])
async def get_task_graph(graph_id: str, session: AsyncSession = Depends(get_session)):
    nodes = await get_graph(session, graph_id)
    return [n.model_dump() for n in nodes]


@router.post("/{graph_id}/cancel")
async def cancel_graph(graph_id: str, session: AsyncSession = Depends(get_session)):
    """Cancel all non-completed tasks in a graph."""
    from sqlmodel import select

    stmt = select(TaskNode).where(
        TaskNode.graph_id == graph_id,
        TaskNode.status.in_(
            [
                TaskStatus.PENDING,
                TaskStatus.THINKING,
                TaskStatus.AWAITING_APPROVAL,
                TaskStatus.WRITING,
                TaskStatus.TESTING,
            ]
        ),
    )
    result = await session.exec(stmt)
    tasks = result.all()

    for task in tasks:
        task.status = TaskStatus.CANCELLED
        session.add(task)

    await session.commit()
    return {"cancelled_count": len(tasks)}


@router.post("/{graph_id}/mutate")
async def mutate_graph(
    graph_id: str, mutation: GraphMutation, session: AsyncSession = Depends(get_session)
):
    """Mutate the task graph structure: rewire, insert, or delete nodes."""
    from sqlmodel import select

    if mutation.action == "rewire":
        if not mutation.task_id:
            return {"error": "task_id is required for rewire"}
        node = await session.get(TaskNode, mutation.task_id)
        if not node:
            return {"error": f"Task {mutation.task_id} not found"}

        if mutation.parent_id == mutation.task_id:
            return {"error": "Cannot rewire a task to be its own parent"}

        node.parent_id = mutation.parent_id
        session.add(node)
        await session.commit()
        await session.refresh(node)
        return {"mutated": True, "action": "rewire", "task": node.model_dump()}

    elif mutation.action == "insert":
        if not (mutation.title and mutation.description and mutation.agent_type):
            return {"error": "title, description, and agent_type are required for insert"}

        new_node = TaskNode(
            graph_id=graph_id,
            parent_id=mutation.parent_id,
            title=mutation.title,
            description=mutation.description,
            agent_type=mutation.agent_type,
            status=TaskStatus.PENDING,
        )
        session.add(new_node)
        await session.commit()
        await session.refresh(new_node)

        if mutation.child_id:
            child = await session.get(TaskNode, mutation.child_id)
            if child:
                child.parent_id = new_node.id
                session.add(child)
                await session.commit()

        return {"mutated": True, "action": "insert", "task": new_node.model_dump()}

    elif mutation.action == "delete":
        if not mutation.task_id:
            return {"error": "task_id is required for delete"}
        node = await session.get(TaskNode, mutation.task_id)
        if not node:
            return {"error": f"Task {mutation.task_id} not found"}

        children_stmt = select(TaskNode).where(TaskNode.parent_id == mutation.task_id)
        children_res = await session.exec(children_stmt)
        children = children_res.all()
        for child in children:
            child.parent_id = node.parent_id
            session.add(child)

        await session.delete(node)
        await session.commit()
        return {"mutated": True, "action": "delete", "task_id": mutation.task_id}

    elif mutation.action == "modify":
        if not mutation.task_id:
            return {"error": "task_id is required for modify"}
        node = await session.get(TaskNode, mutation.task_id)
        if not node:
            return {"error": f"Task {mutation.task_id} not found"}
        if mutation.title:
            node.title = mutation.title
        if mutation.description:
            node.description = mutation.description
        if mutation.agent_type:
            node.agent_type = mutation.agent_type
        session.add(node)
        await session.commit()
        await session.refresh(node)
        return {"mutated": True, "action": "modify", "task": node.model_dump()}

    return {"error": f"Unknown mutation action: {mutation.action}"}


@router.post("/{task_id}/toggle_breakpoint")
async def toggle_breakpoint(task_id: str, session: AsyncSession = Depends(get_session)):
    """Toggle is_checkpoint field for a specific task node."""
    node = await session.get(TaskNode, task_id)
    if not node:
        return {"error": f"Task {task_id} not found"}
    node.is_checkpoint = not node.is_checkpoint
    session.add(node)
    await session.commit()
    await session.refresh(node)
    return {"task_id": task_id, "is_checkpoint": node.is_checkpoint}


@router.post("/{task_id}/approve")
async def approve_single_task(task_id: str, session: AsyncSession = Depends(get_session)):
    """Approve a single task (e.g. bypassing a breakpoint or executing a blocked step)."""
    node = await session.get(TaskNode, task_id)
    if not node:
        return {"error": f"Task {task_id} not found"}

    if node.is_checkpoint:
        node.is_checkpoint = False

    node.status = TaskStatus.PENDING
    session.add(node)
    await session.commit()
    await session.refresh(node)
    return {"task_id": task_id, "status": node.status}
