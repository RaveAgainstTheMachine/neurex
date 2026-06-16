"""
core/task_graph.py
SQLite-backed task graph. Relationships removed to ensure database stability.
The UI can still build the tree view using parent_id.
"""

from __future__ import annotations

import os
import uuid
from collections.abc import AsyncGenerator
from datetime import UTC, datetime
from enum import Enum

from sqlalchemy import event
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine
from sqlalchemy.pool import NullPool
from sqlmodel import Field, SQLModel, select
from sqlmodel.ext.asyncio.session import AsyncSession

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite+aiosqlite:///./neurex.db")

# Phase 44.4: High-Performance SQLite Tuning

pool_args = {}
if os.getenv("TESTING") == "1":
    pool_args["poolclass"] = NullPool

engine = create_async_engine(
    DATABASE_URL, echo=False, connect_args={"check_same_thread": False, "timeout": 30}, **pool_args
)
async_session = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


# Mandatory PRAGMAs for Concurrency & Speed
@event.listens_for(engine.sync_engine, "connect")
def set_sqlite_pragma(dbapi_connection, connection_record):
    cursor = dbapi_connection.cursor()
    cursor.execute("PRAGMA journal_mode=WAL")
    cursor.execute("PRAGMA synchronous=NORMAL")
    cursor.execute("PRAGMA cache_size=-64000")  # 64MB Cache
    cursor.execute("PRAGMA temp_store=MEMORY")
    cursor.execute("PRAGMA mmap_size=30000000000")  # Enable memory mapping
    cursor.close()


class UserRole(str, Enum):
    ADMIN = "admin"  # Full control over Mesh and Settings
    DEVELOPER = "developer"  # Can run agents, edit files, but not change system infra
    VIEWER = "viewer"  # Read-only access to terminal and editor


class User(SQLModel, table=True):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()), primary_key=True)
    username: str = Field(index=True, unique=True)
    hashed_password: str
    role: UserRole = UserRole.DEVELOPER
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    is_active: bool = Field(default=True)
    otp_secret: str | None = None
    otp_enabled: bool = Field(default=False)
    otp_backup_codes: str | None = None  # JSON-serialized list of hashed codes
    force_password_change: bool = Field(default=False)


class InviteCode(SQLModel, table=True):
    code: str = Field(primary_key=True)
    role: UserRole = UserRole.DEVELOPER
    expires_at: datetime
    is_used: bool = Field(default=False)
    created_by: str  # username of admin who created it
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))


class AutonomyLevel(str, Enum):
    RESTRICTED = "restricted"  # Everything needs approval
    LIMITED = "limited"  # Safe commands are auto, unsafe need approval
    STAGING = "staging"  # Staging constraints apply
    FULL = "full"  # Autonomous execution


class TaskStatus(str, Enum):
    PENDING = "pending"
    THINKING = "thinking"
    AWAITING_APPROVAL = "awaiting_approval"
    WRITING = "writing"
    TESTING = "testing"
    DONE = "done"
    FAILED = "failed"
    CANCELLED = "cancelled"


class TaskNode(SQLModel, table=True):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()), primary_key=True)
    parent_id: str | None = Field(default=None, foreign_key="tasknode.id", index=True)
    graph_id: str = Field(index=True)
    agent_type: str
    title: str
    description: str
    status: TaskStatus = TaskStatus.PENDING
    approval_reason: str | None = None  # Why are we waiting?
    result: str | None = None
    error: str | None = None
    iteration: int = 0
    max_iterations: int = 10
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    is_checkpoint: bool = Field(default=False)


class FileLock(SQLModel, table=True):
    path: str = Field(primary_key=True)
    locked_by: str  # user_id or agent_id
    owner_node: str  # Which node instance holds the lock
    expires_at: datetime
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))


class MCPToolPermission(SQLModel, table=True):
    tool_name: str = Field(primary_key=True)
    rule: str = Field(default="ask")  # "allow", "ask", "deny"
    updated_at: datetime = Field(default_factory=lambda: datetime.now(UTC))


class DebateSession(SQLModel, table=True):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()), primary_key=True)
    conversation_id: str = Field(index=True)
    agent_role: str  # "planner", "coder", "reviewer", "judge"
    content: str
    timestamp: datetime = Field(default_factory=lambda: datetime.now(UTC))
    verdict: str | None = Field(default=None)


# DecisionEvent moved to core.observability.flight_recorder
from core.skills.models import PluginHubItem  # noqa: F401


async def init_db():
    async with engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.create_all)


async def get_session() -> AsyncGenerator[AsyncSession, None]:
    async with AsyncSession(engine, expire_on_commit=False) as session:
        yield session


async def create_task(session: AsyncSession, **kwargs) -> TaskNode:
    node = TaskNode(**kwargs)
    session.add(node)
    await session.commit()
    await session.refresh(node)

    # Audit Logging
    import structlog

    log = structlog.get_logger()
    log.info(
        "agent.task_created",
        agent_type=node.agent_type,
        task_id=node.id,
        title=node.title,
        user_id=f"agent:{node.agent_type}",
    )

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
    node.updated_at = datetime.now(UTC)
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

    # Audit Logging
    import structlog

    log = structlog.get_logger()
    log.info(
        "agent.task_updated",
        agent_type=node.agent_type,
        task_id=node.id,
        status=node.status,
        user_id=f"agent:{node.agent_type}",
        error=node.error if node.error else None,
    )

    return node


async def get_graph(session: AsyncSession, graph_id: str) -> list[TaskNode]:
    result = await session.exec(select(TaskNode).where(TaskNode.graph_id == graph_id))
    return list(result.all())


def is_stalled(node: TaskNode, last_tool_call: dict | None, current_tool_call: dict | None) -> bool:
    if node.iteration >= node.max_iterations:
        return True
    if last_tool_call and current_tool_call:
        return last_tool_call == current_tool_call
    return False
