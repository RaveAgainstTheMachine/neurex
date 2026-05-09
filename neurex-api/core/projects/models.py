from __future__ import annotations

import random
import uuid
from datetime import datetime
from enum import Enum

from sqlmodel import Field, SQLModel


class ProjectRole(str, Enum):
    OWNER     = "owner"      # Full control, can delete project, manage users
    ADMIN     = "admin"      # Can manage users and settings
    MEMBER    = "member"     # Can create tasks, edit files
    VIEWER    = "viewer"     # Read-only access
    AGENT     = "agent"      # Autonomous agent with task-management permissions

def generate_random_color() -> str:
    """Generate a random vivid hex color for user presence."""
    return f"hsl({random.randint(0, 360)}, 85%, 65%)"

class Project(SQLModel, table=True):
    """A collaborative workspace/project."""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()), primary_key=True)
    name: str = Field(index=True)
    description: str | None = Field(default=None)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    is_active: bool = Field(default=True)

class ProjectMember(SQLModel, table=True):
    """Link between a User and a Project, storing their specific role and assigned color."""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()), primary_key=True)
    project_id: str = Field(foreign_key="project.id", index=True)
    user_id: str = Field(foreign_key="user.id", index=True)
    
    role: ProjectRole = Field(default=ProjectRole.MEMBER)
    color: str = Field(default_factory=generate_random_color) # Immutable per project
    joined_at: datetime = Field(default_factory=datetime.utcnow)

class ProjectTaskStatus(str, Enum):
    TODO        = "todo"
    IN_PROGRESS = "in_progress"
    REVIEW      = "review"
    DONE        = "done"

class ProjectTask(SQLModel, table=True):
    """A Project Management ticket (distinct from the Orchestrator's internal TaskNode execution graph)."""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()), primary_key=True)
    project_id: str = Field(foreign_key="project.id", index=True)
    
    title: str
    description: str | None = Field(default=None)
    status: ProjectTaskStatus = Field(default=ProjectTaskStatus.TODO)
    
    created_by: str = Field(foreign_key="user.id")
    assignee_id: str | None = Field(default=None, foreign_key="user.id")
    
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
