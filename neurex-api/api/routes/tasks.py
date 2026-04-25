"""api/routes/tasks.py — Task graph REST endpoints."""
from fastapi import APIRouter, Depends
from core.task_graph import get_session, get_graph, TaskNode, AsyncSession
from typing import List

router = APIRouter()


@router.get("/", response_model=List[dict])
async def list_tasks(graph_id: str | None = None, session: AsyncSession = Depends(get_session)):
    from sqlmodel import select
    from core.task_graph import TaskNode
    
    query = select(TaskNode)
    if graph_id:
        query = query.where(TaskNode.graph_id == graph_id)
    
    result = await session.exec(query.order_by(TaskNode.created_at.desc()))
    return [n.model_dump() for n in result.all()]

@router.delete("/", response_model=dict)
async def delete_all_tasks(session: AsyncSession = Depends(get_session)):
    from sqlmodel import delete
    from core.task_graph import TaskNode
    await session.exec(delete(TaskNode))
    await session.commit()
    return {"deleted": True}

@router.post("/{graph_id}/approve_all")
async def approve_all_tasks(graph_id: str, session: AsyncSession = Depends(get_session)):
    """Approve all PENDING or AWAITING_APPROVAL tasks in a graph."""
    from sqlmodel import select
    from core.task_graph import TaskNode, TaskStatus
    
    stmt = select(TaskNode).where(
        TaskNode.graph_id == graph_id,
        TaskNode.status.in_([TaskStatus.AWAITING_APPROVAL, TaskStatus.PENDING])
    )
    result = await session.exec(stmt)
    tasks = result.all()
    
    for task in tasks:
        # If it's the planner, we transition it to DONE to let resume() pick up children
        # If it's a subtask, we let resume() handle it
        task.status = TaskStatus.PENDING
        session.add(task)
        
    await session.commit()
    return {"approved_count": len(tasks)}

@router.get("/{graph_id}", response_model=List[dict])

async def get_task_graph(graph_id: str, session: AsyncSession = Depends(get_session)):
    nodes = await get_graph(session, graph_id)
    return [n.model_dump() for n in nodes]

