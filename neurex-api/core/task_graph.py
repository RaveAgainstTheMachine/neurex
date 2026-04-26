"""
core/task_graph.py
SQLite-backed task graph. Relationships removed to ensure database stability.
The UI can still build the tree view using parent_id.
"""
from __future__ import annotations
import uuid
from datetime import datetime
from enum import Enum
from typing import Optional, List

from sqlmodel import SQLModel, Field, select
from sqlmodel.ext.asyncio.session import AsyncSession
from sqlalchemy.ext.asyncio import create_async_engine

DATABASE_URL = "sqlite+aiosqlite:///./neurex.db"
engine = create_async_engine(DATABASE_URL, echo=False)

class UserRole(str, Enum):
    ADMIN     = "admin"      # Full control over Mesh and Settings
    DEVELOPER = "developer"  # Can run agents, edit files, but not change system infra
    VIEWER    = "viewer"     # Read-only access to terminal and editor

class User(SQLModel, table=True):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()), primary_key=True)
    username: str = Field(index=True, unique=True)
    hashed_password: str
    role: UserRole = UserRole.DEVELOPER
    created_at: datetime = Field(default_factory=datetime.utcnow)
    is_active: bool = Field(default=True)

class AutonomyLevel(str, Enum):
    RESTRICTED = "restricted" # Everything needs approval
    LIMITED    = "limited"    # Safe commands are auto, unsafe need approval
    FULL       = "full"       # Autonomous execution

class TaskStatus(str, Enum):
    PENDING   = "pending"
    THINKING  = "thinking"
    AWAITING_APPROVAL = "awaiting_approval"
    WRITING   = "writing"
    TESTING   = "testing"
    DONE      = "done"
    FAILED    = "failed"
    CANCELLED = "cancelled"

class TaskNode(SQLModel, table=True):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()), primary_key=True)
    parent_id: Optional[str] = Field(default=None, foreign_key="tasknode.id", index=True)
    graph_id: str = Field(index=True)
    agent_type: str
    title: str
    description: str
    status: TaskStatus = TaskStatus.PENDING
    approval_reason: Optional[str] = None # Why are we waiting?
    result: Optional[str] = None
    error: Optional[str] = None
    iteration: int = 0
    max_iterations: int = 10
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

async def init_db():
    import core.projects.models # Ensure models are registered with SQLModel
    async with engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.create_all)

async def get_session() -> AsyncSession:
    async with AsyncSession(engine) as session:
        yield session

async def create_task(session: AsyncSession, **kwargs) -> TaskNode:
    node = TaskNode(**kwargs)
    session.add(node)
    await session.commit()
    await session.refresh(node)
    return node

async def update_task(
    session: AsyncSession,
    task_id: str,
    status: TaskStatus,
    result: str | None = None,
    error: str | None = None,
    approval_reason: str | None = None,
) -> TaskNode | None:
    node = await session.get(TaskNode, task_id)
    if not node:
        return None
    node.status = status
    node.updated_at = datetime.utcnow()
    node.iteration += 1
    if result is not None:
        node.result = result
    if error is not None:
        node.error = error
    if approval_reason is not None:
        node.approval_reason = approval_reason
    session.add(node)
    await session.commit()
    await session.refresh(node)
    return node

async def get_graph(session: AsyncSession, graph_id: str) -> List[TaskNode]:
    result = await session.exec(
        select(TaskNode).where(TaskNode.graph_id == graph_id)
    )
    return result.all()

def is_stalled(node: TaskNode, last_tool_call: dict | None, current_tool_call: dict | None) -> bool:
    if node.iteration >= node.max_iterations:
        return True
    if last_tool_call and current_tool_call:
        return last_tool_call == current_tool_call
    return False
