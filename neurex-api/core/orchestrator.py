"""
core/orchestrator.py
Supervisor agent. Parses a user request into a TaskGraph, then delegates
sub-tasks to specialized agents and streams status updates over a websocket.
Supports Human-in-the-Loop for plan approval.
"""
from __future__ import annotations
import json
import uuid
import structlog
from typing import AsyncGenerator, List, Dict, Any

from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession

from core.task_graph import (
    TaskNode, TaskStatus, create_task, update_task,
    get_graph, is_stalled
)
from core.agents.planner_agent import PlannerAgent
from core.agents.coder_agent import CoderAgent
from core.agents.tester_agent import TesterAgent
from core.agents.researcher_agent import ResearcherAgent
from core.agents.reviewer_agent import ReviewerAgent

from core.context.manager import ContextManager
from core.context.rules_parser import RulesParser

log = structlog.get_logger()

AGENT_MAP = {
    "planner":    PlannerAgent,
    "coder":      CoderAgent,
    "tester":     TesterAgent,
    "researcher": ResearcherAgent,
    "reviewer":   ReviewerAgent,
}

class Orchestrator:
    def __init__(
        self,
        session: AsyncSession,
        rules: RulesParser,
        context_manager: ContextManager,
    ):
        self.session = session
        self.rules = rules
        self.ctx = context_manager

    async def run(
        self,
        user_message: str,
        conversation_id: str,
    ) -> AsyncGenerator[dict, None]:
        """Phase 1: Planning and Decomposition."""
        graph_id = str(uuid.uuid4())
        log.info("orchestrator.plan", graph_id=graph_id)

        planner_node = await create_task(
            self.session,
            graph_id=graph_id,
            agent_type="planner",
            title="Plan",
            description=user_message,
        )
        yield {"event": "task_created", "data": planner_node.model_dump()}

        planner = PlannerAgent(self.rules, self.ctx)
        plan: list[dict] = []

        await update_task(self.session, planner_node.id, TaskStatus.THINKING)
        yield {"event": "task_updated", "data": {"id": planner_node.id, "status": TaskStatus.THINKING}}

        async for chunk in planner.plan(user_message, conversation_id):
            if chunk["type"] == "token":
                yield {"event": "token", "data": chunk["text"]}
            elif chunk["type"] == "result":
                plan = chunk["plan"]

        # Create all sub-tasks as PENDING
        for step in plan:
            agent_type = step.get("agent", "coder")
            await create_task(
                self.session,
                graph_id=graph_id,
                parent_id=planner_node.id,
                agent_type=agent_type,
                title=step.get("title", agent_type),
                description=step.get("description", ""),
            )

        # Set planner to AWAITING_APPROVAL
        await update_task(
            self.session, planner_node.id, TaskStatus.AWAITING_APPROVAL,
            result=json.dumps(plan)
        )
        
        # Reload graph to send to UI
        graph = await get_graph(self.session, graph_id)
        yield {"event": "plan_ready", "data": {
            "graph_id": graph_id,
            "tasks": [n.model_dump() for n in graph]
        }}

    async def resume(
        self,
        graph_id: str,
        conversation_id: str,
    ) -> AsyncGenerator[dict, None]:
        """Phase 2: Execution after approval."""
        log.info("orchestrator.resume", graph_id=graph_id)
        
        # Get all non-done, non-planner tasks in this graph
        stmt = select(TaskNode).where(
            TaskNode.graph_id == graph_id,
            TaskNode.agent_type != "planner",
            TaskNode.status == TaskStatus.PENDING
        ).order_by(TaskNode.created_at)
        
        result = await self.session.exec(stmt)
        tasks = result.all()
        
        last_tool_calls: dict[str, dict | None] = {}

        for node in tasks:
            AgentClass = AGENT_MAP.get(node.agent_type, CoderAgent)
            agent = AgentClass(self.rules, self.ctx)
            
            step = {"description": node.description, "title": node.title}
            last_tool_call = last_tool_calls.get(node.id)

            async for chunk in agent.execute(step, conversation_id):
                if chunk["type"] == "tool_call":
                    if is_stalled(node, last_tool_call, chunk["call"]):
                        await update_task(self.session, node.id, TaskStatus.FAILED, error="Stall detected")
                        yield {"event": "task_updated", "data": {"id": node.id, "status": TaskStatus.FAILED}}
                        break
                    last_tool_calls[node.id] = chunk["call"]

                if chunk["type"] == "status":
                    await update_task(self.session, node.id, chunk["status"])
                    yield {"event": "task_updated", "data": {"id": node.id, "status": chunk["status"]}}
                elif chunk["type"] == "token":
                    yield {"event": "token", "data": chunk["text"]}
                elif chunk["type"] == "result":
                    await update_task(self.session, node.id, TaskStatus.DONE, result=chunk.get("result", ""))
                    yield {"event": "task_updated", "data": {"id": node.id, "status": TaskStatus.DONE}}

        # Final cleanup
        graph = await get_graph(self.session, graph_id)
        yield {"event": "done", "data": {
            "graph_id": graph_id,
            "tasks": [n.model_dump() for n in graph]
        }}
