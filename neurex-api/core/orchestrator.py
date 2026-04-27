"""
core/orchestrator.py
Supervisor agent. Parses a user request into a TaskGraph, then delegates
sub-tasks to specialized agents and streams status updates over a websocket.
Supports Human-in-the-Loop for plan approval.
"""
from __future__ import annotations
import json
import uuid
import os
from pathlib import Path
import structlog
from typing import AsyncGenerator, List, Dict, Any

from fastapi.encoders import jsonable_encoder
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
from core.agents.debater_agent import DebaterAgent

from core.context.manager import ContextManager
from core.context.rules_parser import RulesParser
from core.infrastructure.registry import LLMRecommender
from core.infrastructure.manager import InfrastructureManager
from core.memory.hive import hive_mind

log = structlog.get_logger()

AGENT_MAP = {
    "planner":    PlannerAgent,
    "coder":      CoderAgent,
    "tester":     TesterAgent,
    "researcher": ResearcherAgent,
    "reviewer":   ReviewerAgent,
    "debater":    DebaterAgent,
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
        self.infra = InfrastructureManager()
        self.workspace = Path(os.getenv("WORKSPACE_PATH", "/workspace"))
        self.autonomy_level = os.getenv("AUTONOMY_CEILING", "limited")

    def set_autonomy_level(self, level: str):
        """Override the session-specific autonomy level."""
        self.autonomy_level = level

    async def _create_git_snapshot(self, graph_id: str):
        """Creates a git tag/snapshot of the workspace for safety."""
        import subprocess
        try:
            # Check if git is initialized
            subprocess.run(["git", "rev-parse", "--is-inside-work-tree"], cwd=self.workspace, check=True, capture_output=True)
            
            # Create a snapshot tag
            tag_name = f"neurex-pre-{graph_id[:8]}"
            subprocess.run(["git", "add", "."], cwd=self.workspace, check=True)
            # Use --allow-empty in case there are no changes
            subprocess.run(["git", "commit", "-m", f"Neurex Safe Snapshot: {graph_id}"], cwd=self.workspace, capture_output=True)
            subprocess.run(["git", "tag", tag_name], cwd=self.workspace, check=True)
            log.info("safety.snapshot_created", tag=tag_name)
        except Exception as e:
            log.warning("safety.snapshot_failed", error=str(e), hint="Is git initialized in the workspace?")

    async def run(
        self,
        user_message: str,
        conversation_id: str,
        model: str | None = None,
    ) -> AsyncGenerator[dict, None]:
        """Phase 1: Planning and Decomposition."""
        graph_id = str(uuid.uuid4())
        log.info("orchestrator.plan", graph_id=graph_id)
        
        # Rogue Agent Safeguard: Create a git snapshot before starting
        await self._create_git_snapshot(graph_id)

        planner_node = await create_task(
            self.session,
            graph_id=graph_id,
            agent_type="planner",
            title="Plan",
            description=user_message,
        )
        yield {"event": "task_created", "data": jsonable_encoder(planner_node)}


        vram = self.infra.get_system_vram()
        rec = LLMRecommender.recommend("planning", vram)
        model_name = model or (rec.name if rec else None)
        
        log.info("orchestrator.using_model", agent="planner", model=model_name, source="user" if model else "rec")
        
        # Consult Hive Mind for context
        memories = hive_mind.recall(user_message, limit=3)
        hive_context = "\n".join([f"- {m['content']}" for m in memories]) if memories else "No relevant memories found."
        
        planner = PlannerAgent(self.rules, self.ctx, model=model_name)
        # Inject memories into the planning context
        augmented_message = f"Relevant project history:\n{hive_context}\n\nUser request: {user_message}"
        
        plan: list[dict] = []

        await update_task(self.session, planner_node.id, TaskStatus.THINKING)
        yield {"event": "task_updated", "data": {"id": planner_node.id, "status": TaskStatus.THINKING}}

        async for chunk in planner.plan(augmented_message, conversation_id):
            if chunk["type"] == "token":
                yield {"event": "token", "data": chunk["text"]}
            elif chunk["type"] == "result":
                plan = chunk["plan"]

        log.info("orchestrator.plan_received", steps_count=len(plan))
        for i, step in enumerate(plan):
            agent_type = step.get("agent", "coder")
            log.info("orchestrator.creating_subtask", step=i, agent=agent_type, title=step.get("title"))
            await create_task(
                self.session,
                graph_id=graph_id,
                parent_id=planner_node.id,
                agent_type=agent_type,
                title=step.get("title", agent_type),
                description=step.get("description", ""),
            )
            await self.session.commit()


        # Set planner to AWAITING_APPROVAL
        await update_task(
            self.session, planner_node.id, TaskStatus.AWAITING_APPROVAL,
            result=json.dumps(plan)
        )
        
        from api.routes.notifications import send_notification
        send_notification(
            title="Plan Ready",
            body=f"Neurex has created a plan for: {planner_node.title}"
        )
        
        # Reload graph to send to UI
        graph = await get_graph(self.session, graph_id)
        yield {"event": "plan_ready", "data": {
            "graph_id": graph_id,
            "tasks": [jsonable_encoder(n) for n in graph]
        }}


    async def resume(
        self,
        graph_id: str,
        conversation_id: str,
    ) -> AsyncGenerator[dict, None]:
        """Phase 2: Execution after approval."""
        log.info("orchestrator.resume", graph_id=graph_id)
        
        last_tool_calls: dict[str, dict | None] = {}

        while True:
            # 0. Check if graph has been cancelled
            cancel_stmt = select(TaskNode).where(
                TaskNode.graph_id == graph_id,
                TaskNode.status == TaskStatus.CANCELLED
            )
            cancel_result = await self.session.exec(cancel_stmt)
            if cancel_result.first():
                log.info("orchestrator.halted", graph_id=graph_id, reason="cancelled")
                yield {"event": "graph_cancelled", "data": {"graph_id": graph_id}}
                break

            # 1. Re-fetch tasks that are PENDING and belong to this graph
            stmt = select(TaskNode).where(
                TaskNode.graph_id == graph_id,
                TaskNode.agent_type != "planner",
                TaskNode.status == TaskStatus.PENDING
            ).order_by(TaskNode.created_at)
            
            result = await self.session.exec(stmt)
            tasks = result.all()
            
            if not tasks:
                break

            for node in tasks:
                vram = self.infra.get_system_vram()
                rec = LLMRecommender.recommend(node.agent_type, vram)
                model_name = rec.name if rec else None
                
                log.info("orchestrator.using_model", agent=node.agent_type, model=model_name, task=node.title)
                
                AgentClass = AGENT_MAP.get(node.agent_type, CoderAgent)
                agent = AgentClass(self.rules, self.ctx, model=model_name)
                
                # 1. Primary Execution
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
                        node_result = chunk.get("result", "")
                        status = TaskStatus.DONE
                        
                        if "APPROVAL_REQUIRED" in node_result:
                            status = TaskStatus.AWAITING_APPROVAL
                            reason = node_result.replace("APPROVAL_REQUIRED:", "").strip()
                            from api.routes.notifications import send_notification
                            send_notification(
                                title="Action Required",
                                body=reason
                            )
                            await update_task(self.session, node.id, status, result=node_result, approval_reason=reason)
                        else:
                            await update_task(self.session, node.id, status, result=node_result)
                            # Index successful outcome in Hive Mind
                            hive_mind.remember(
                                content=f"Task: {node.title}\nDescription: {node.description}\nResult: {node_result}",
                                metadata={"agent": node.agent_type, "graph_id": graph_id, "conversation_id": conversation_id},
                                doc_id=f"outcome-{node.id}"
                            )
                        yield {"event": "task_updated", "data": {"id": node.id, "status": status}}

                        # 2. Quality Gate (Reviewer loop)
                        if node.agent_type in ("coder", "tester") and node.iteration < 3:
                            log.info("orchestrator.review_gate", task_id=node.id)
                            
                            r_rec = LLMRecommender.recommend("reviewer", vram)
                            r_model = r_rec.name if r_rec else None
                            log.info("orchestrator.using_model", agent="reviewer", model=r_model)
                            
                            reviewer = ReviewerAgent(self.rules, self.ctx, model=r_model)
                            review_task = {
                                "title": f"Review: {node.title}",
                                "description": f"Goal: {node.description}\nResult: {node_result}"
                            }
                            
                            review_feedback = ""
                            async for rchunk in reviewer.execute(review_task, conversation_id):
                                if rchunk["type"] == "token":
                                    yield {"event": "token", "data": rchunk["text"]}
                                if rchunk["type"] == "result":
                                    review_feedback = rchunk["result"]
                            
                            if "APPROVE" not in review_feedback.upper():
                                log.info("orchestrator.review_failed", task_id=node.id)
                                # Reset node to PENDING with feedback to force re-run
                                await update_task(
                                    self.session, node.id, TaskStatus.PENDING,
                                    error=f"Review failed: {review_feedback}"
                                )
                                yield {"event": "task_updated", "data": {"id": node.id, "status": TaskStatus.PENDING}}
                                # Task is now PENDING again, while loop will catch it in next iteration
                                break

        # Final cleanup
        graph = await get_graph(self.session, graph_id)
        yield {"event": "done", "data": {
            "graph_id": graph_id,
            "tasks": [jsonable_encoder(n) for n in graph]
        }}

    async def resume_shell(
        self,
        task_id: str,
        approved: bool,
        conversation_id: str,
    ) -> AsyncGenerator[dict, None]:
        """Phase 3: Resuming a task after a shell approval."""
        node = await self.session.get(TaskNode, task_id)
        if not node: return

        log.info("orchestrator.resume_shell", task_id=task_id, approved=approved)

        if not approved:
            await update_task(self.session, node.id, TaskStatus.FAILED, error="User denied shell command")
            yield {"event": "task_updated", "data": {"id": node.id, "status": TaskStatus.FAILED}}
            return

        # Clear the approval required flag in the result before resuming
        node.result = ""
        self.session.add(node)
        await self.session.commit()

        # Re-run execution with approved flag
        vram = self.infra.get_system_vram()
        rec = LLMRecommender.recommend(node.agent_type, vram)
        model_name = rec.name if rec else None
        
        log.info("orchestrator.using_model", agent=node.agent_type, model=model_name, task=node.title, mode="resume_shell")
        
        AgentClass = AGENT_MAP.get(node.agent_type, CoderAgent)
        agent = AgentClass(self.rules, self.ctx, model=model_name)
        
        # We pass approved=True to the task description or a context object
        step = {"description": f"{node.description}\n[USER APPROVED SHELL EXECUTION]", "title": node.title}
        
        async for chunk in agent.execute(step, conversation_id):
            if chunk["type"] == "status":
                await update_task(self.session, node.id, chunk["status"])
                yield {"event": "task_updated", "data": {"id": node.id, "status": chunk["status"]}}
            elif chunk["type"] == "token":
                yield {"event": "token", "data": chunk["text"]}
            elif chunk["type"] == "result":
                await update_task(self.session, node.id, TaskStatus.DONE, result=chunk.get("result", ""))
                yield {"event": "task_updated", "data": {"id": node.id, "status": TaskStatus.DONE}}
