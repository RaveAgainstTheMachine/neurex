"""api/routes/tasks.py — Task graph REST endpoints."""
from fastapi import APIRouter, Depends
from core.task_graph import get_session, get_graph, TaskNode, AsyncSession
from typing import List

router = APIRouter()


@router.get("/", response_model=List[dict])
async def list_all_tasks(session: AsyncSession = Depends(get_session)):
    from sqlmodel import select
    from core.task_graph import TaskNode
    result = await session.exec(select(TaskNode).order_by(TaskNode.created_at.desc()))
    return [n.model_dump() for n in result.all()]

@router.delete("/", response_model=dict)
async def delete_all_tasks(session: AsyncSession = Depends(get_session)):
    from sqlmodel import delete
    from core.task_graph import TaskNode
    await session.exec(delete(TaskNode))
    await session.commit()
    return {"deleted": True}

@router.get("/{graph_id}", response_model=List[dict])

async def get_task_graph(graph_id: str, session: AsyncSession = Depends(get_session)):
    nodes = await get_graph(session, graph_id)
    return [n.model_dump() for n in nodes]

