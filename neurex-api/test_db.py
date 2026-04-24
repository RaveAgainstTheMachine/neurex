from __future__ import annotations
import asyncio
from typing import Optional, List
from sqlmodel import SQLModel, Field, Relationship, Session, create_engine, select
from sqlalchemy.orm import Mapped

# SQLite engine (sync for simple test)
engine = create_engine("sqlite:///test_neurex.db")

class TaskNode(SQLModel, table=True):
    id: str = Field(default="root", primary_key=True)
    parent_id: Optional[str] = Field(default=None, foreign_key="tasknode.id")
    
    # Correct SQLModel 0.0.22+ syntax for self-referential
    parent: Optional[TaskNode] = Relationship(
        back_populates="children",
        sa_relationship_kwargs={"remote_side": "TaskNode.id"}
    )
    children: List[TaskNode] = Relationship(
        back_populates="parent"
    )

def test():
    SQLModel.metadata.drop_all(engine)
    SQLModel.metadata.create_all(engine)
    with Session(engine) as session:
        root = TaskNode(id="root")
        child = TaskNode(id="child", parent_id="root")
        session.add(root)
        session.add(child)
        session.commit()
        print("Success!")

if __name__ == "__main__":
    test()
