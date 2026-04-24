"""api/routes/tasks.py — Task graph REST endpoints."""
from fastapi import APIRouter, Depends
from core.task_graph import get_session, get_graph, TaskNode, AsyncSession
from typing import List

router = APIRouter()


@router.get("/{graph_id}", response_model=List[dict])
async def get_task_graph(graph_id: str, session: AsyncSession = Depends(get_session)):
    nodes = await get_graph(session, graph_id)
    return [n.model_dump() for n in nodes]
