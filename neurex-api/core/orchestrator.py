"""
core/orchestrator.py
Supervisor agent. Parses a user request into a TaskGraph, then delegates
sub-tasks to specialized agents and streams status updates over a websocket.
Supports Human-in-the-Loop for plan approval.
"""
from __future__ import annotations

import json
import os
import uuid
from collections.abc import AsyncGenerator
from pathlib import Path

import structlog
from fastapi.encoders import jsonable_encoder
from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession

from core.agents.coder_agent import CoderAgent
from core.agents.commander_agent import CommanderAgent
from core.agents.debater_agent import DebaterAgent
from core.agents.planner_agent import PlannerAgent
from core.agents.researcher_agent import ResearcherAgent
from core.agents.reviewer_agent import ReviewerAgent
from core.agents.swarm_agent import SwarmAgent
from core.agents.tester_agent import TesterAgent
from core.context.manager import ContextManager
from core.context.rules_parser import RulesParser
from core.infrastructure.manager import InfrastructureManager
from core.memory.hive import hive_mind
from core.task_graph import TaskNode, TaskStatus, create_task, get_graph, update_task

log = structlog.get_logger()

AGENT_MAP = {
    "planner":    PlannerAgent,
    "coder":      CoderAgent,
    "tester":     TesterAgent,
    "researcher": ResearcherAgent,
    "reviewer":   ReviewerAgent,
    "debater":    DebaterAgent,
    "commander":  CommanderAgent,
    "swarm":      SwarmAgent,
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

    async def _summarize_history(self, tasks: list[TaskNode], model: str) -> str:
        """Condense a long task history into a manageable summary."""
        if not tasks:
            return ""
        
        history_text = "\n".join([f"Task: {n.title}\nResult: {n.result}" for n in tasks])
        
        # If history is small (e.g. < 4k chars), return as-is
        if len(history_text) < 4000:
            return history_text
            
        log.info("orchestrator.summarizing_context", task_count=len(tasks), char_count=len(history_text))
        
        from core.agents.reviewer_agent import ReviewerAgent
        summarizer = ReviewerAgent(self.rules, self.ctx, model=model)
        
        prompt = f"Summarize the following completed task steps into a concise summary for a sibling agent. Focus on what was achieved and any critical findings:\n\n{history_text}"
        
        summary = ""
        # Use a simple stream collect
        async for chunk in summarizer.stream([{"role": "user", "content": prompt}]):
            if chunk["type"] == "token":
                summary += chunk["text"]
            elif chunk["type"] == "done":
                break
        
        # Return summary + the very last result in full for immediate context
        return f"[CONTEXT SUMMARY]\n{summary}\n\n[LATEST RESULT]\nTask: {tasks[-1].title}\nResult: {tasks[-1].result}"

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
        try:
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


            from core.settings.manager import settings_manager
            routes = settings_manager.get("model_routes") or {}
            model_name = model or routes.get("Planning") or settings_manager.get("planner_model")
            
            # Resolve params for planner
            if isinstance(model_name, dict):
                model_params = model_name.get("params")
                model_name = model_name.get("model")
            else:
                model_params = await self.infra.resolve_model_params(model_name)
                if model_params == "Unknown":
                    model_params = None
            
            log.info("orchestrator.using_model", agent="planner", model=model_name, source="user" if model else "routes")
            
            # Consult Hive Mind for context
            memories = hive_mind.recall(user_message, limit=3)
            hive_context = "\n".join([f"- {m['content']}" for m in memories]) if memories else "No relevant memories found."
            
            planner = PlannerAgent(self.rules, self.ctx, model=model_name)
            # Inject memories into the planning context
            augmented_message = f"Relevant project history:\n{hive_context}\n\nUser request: {user_message}"
            
            plan: list[dict] = []

            await update_task(self.session, planner_node.id, TaskStatus.THINKING)
            yield {"event": "task_updated", "data": {"id": planner_node.id, "status": TaskStatus.THINKING}}

            async for chunk in planner.plan(augmented_message, conversation_id, params=model_params):
                if chunk["type"] == "token":
                    yield {"event": "token", "data": chunk["text"]}
                elif chunk["type"] == "result":
                    plan = chunk["plan"]

            log.info("orchestrator.plan_received", steps_count=len(plan))
            
            if len(plan) == 1 and plan[0].get("agent") == "chat":
                # Direct conversational reply - bypass task approval
                await update_task(self.session, planner_node.id, TaskStatus.DONE, result=plan[0]["description"])
                yield {"event": "chat_reply", "data": plan[0]["description"]}
                yield {"event": "graph_complete", "data": {"graph_id": graph_id}}
                return

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
        except Exception as e:
            log.critical("orchestrator.run_crashed", graph_id=graph_id, error=str(e), exc_info=True)
            yield {"event": "error", "data": {"message": f"Critical planning failure: {str(e)}"}}


    async def resume(
        self,
        graph_id: str,
        conversation_id: str,
    ) -> AsyncGenerator[dict, None]:
        """Phase 2: Execution after approval."""
        log.info("orchestrator.resume", graph_id=graph_id)
        
        last_tool_calls: dict[str, dict | None] = {}
        active_node_id = None

        try:
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
                    log.info("orchestrator.graph_complete", graph_id=graph_id)
                    yield {"event": "graph_complete", "data": {"graph_id": graph_id}}
                    break

                for node in tasks:
                    try:
                        active_node_id = node.id
                        log.info("orchestrator.executing_task", task_id=node.id, title=node.title)
                        await update_task(self.session, node.id, TaskStatus.THINKING)
                        yield {"event": "task_updated", "data": {"id": node.id, "status": TaskStatus.THINKING}}
    
                        from core.settings.manager import settings_manager
                    
                        # Phase 60: Resolve model via Route Map
                        role_map = {
                            "planner":    "Planning",
                            "coder":      "Coding",
                            "tester":     "Testing",
                            "researcher": "Researching",
                            "reviewer":   "Reviewing",
                            "debater":    "Reviewing", # Shared route
                            "commander":  "Planning",  # Shared route
                            "swarm":      "Coding"     # Shared route
                        }
                        
                        routes = settings_manager.get("model_routes") or {}
                        target_role = role_map.get(node.agent_type, "Coding")
                        route_config = routes.get(target_role) or settings_manager.get(f"{node.agent_type}_model")
                        
                        # Phase 61: Structured Route Resolution (Model + Params)
                        if isinstance(route_config, dict):
                            model_name = route_config.get("model")
                            model_params = route_config.get("params")
                        else:
                            model_name = route_config
                            model_params = None
                        
                        # Phase 61.1: Derive params if missing
                        if not model_params and model_name:
                            model_params = await self.infra.resolve_model_params(model_name)
                            if model_params == "Unknown":
                                model_params = None
                        
                        log.info("orchestrator.using_model", 
                                 agent=node.agent_type, 
                                 role=target_role, 
                                 model=model_name,
                                 params=model_params,
                                 task=node.title)
    
                        AgentClass = AGENT_MAP.get(node.agent_type, CoderAgent)
                        agent = AgentClass(self.rules, self.ctx, model=model_name)
                        
                        # Gather and summarize history context
                        history_stmt = select(TaskNode).where(
                            TaskNode.graph_id == graph_id,
                            TaskNode.status == TaskStatus.DONE
                        ).order_by(TaskNode.created_at)
                        history_result = await self.session.exec(history_stmt)
                        done_tasks = history_result.all()
                        
                        history_context = await self._summarize_history(done_tasks, model_name)
                        
                        task_payload = {
                            "id": node.id,
                            "title": node.title,
                            "description": node.description,
                            "context": node.context,
                            "history": history_context,
                            "model": model_name,
                            "params": model_params,
                            "last_tool_call": last_tool_calls.get(node.id)
                        }
    
                        node_result = ""
                        async for chunk in agent.execute(task_payload, conversation_id):
                            if chunk["type"] == "token":
                                yield {"event": "token", "data": chunk["text"], "task_id": node.id}
                            elif chunk["type"] == "status":
                                yield {"event": "task_status", "data": {"id": node.id, "status": chunk["status"]}}
                            elif chunk["type"] == "tool_call":
                                if self.autonomy_level == "limited" and chunk["tool"] in ["shell", "filesystem"]:
                                    log.info("orchestrator.hitl_required", tool=chunk["tool"])
                                    await update_task(self.session, node.id, TaskStatus.AWAITING_APPROVAL)
                                    yield {
                                        "event": "approval_required", 
                                        "data": {
                                            "id": node.id, 
                                            "tool": chunk["tool"], 
                                            "args": chunk["args"]
                                        }
                                    }
                                    last_tool_calls[node.id] = chunk
                                    return 
    
                            elif chunk["type"] == "result":
                                node_result = chunk["result"]
    
                        # Mark as DONE
                        await update_task(self.session, node.id, TaskStatus.DONE, result=node_result)
                        yield {"event": "task_updated", "data": {"id": node.id, "status": TaskStatus.DONE}}
                        
                        hive_mind.remember(
                            content=f"Completed task '{node.title}' in graph {graph_id}. Result: {node_result}",
                            metadata={"graph_id": graph_id, "agent_type": node.agent_type, "type": "task_result"},
                            doc_id=node.id
                        )
                        active_node_id = None

                    except Exception as e:
                        log.error("orchestrator.task_failed", task_id=node.id, error=str(e))
                        await update_task(self.session, node.id, TaskStatus.FAILED, error=str(e))
                        yield {"event": "task_updated", "data": {"id": node.id, "status": TaskStatus.FAILED}}
                        active_node_id = None
                        continue
        except Exception as e:
            log.critical("orchestrator.resume_crashed", graph_id=graph_id, error=str(e), exc_info=True)
            if active_node_id:
                try:
                    await update_task(self.session, active_node_id, TaskStatus.FAILED, error=f"Orchestrator crash: {str(e)}")
                except Exception as update_err:
                    log.error("orchestrator.crash_update_failed", error=str(update_err))
                    pass
            yield {"event": "error", "data": {"message": f"Critical execution failure: {str(e)}"}}

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
        try:
            node = await self.session.get(TaskNode, task_id)
            if not node: return

            log.info("orchestrator.resume_shell", task_id=task_id, approved=approved)

            if not approved:
                await update_task(self.session, node.id, TaskStatus.FAILED, error="User denied shell command")
                yield {"event": "task_updated", "data": {"id": node.id, "status": TaskStatus.FAILED}}
                return

            node.result = ""
            self.session.add(node)
            await self.session.commit()

            from core.settings.manager import settings_manager
            settings_key = f"{node.agent_type}_model"
            model_name = settings_manager.get(settings_key)
            
            # Resolve params
            model_params = await self.infra.resolve_model_params(model_name)
            if model_params == "Unknown":
                model_params = None
            
            AgentClass = AGENT_MAP.get(node.agent_type, CoderAgent)
            agent = AgentClass(self.rules, self.ctx, model=model_name)
            
            step = {
                "id": node.id,
                "description": f"{node.description}\n[USER APPROVED SHELL EXECUTION]", 
                "title": node.title,
                "params": model_params
            }
            
            async for chunk in agent.execute(step, conversation_id):
                if chunk["type"] == "status":
                    await update_task(self.session, node.id, chunk["status"])
                    yield {"event": "task_updated", "data": {"id": node.id, "status": chunk["status"]}}
                elif chunk["type"] == "token":
                    yield {"event": "token", "data": chunk["text"]}
                elif chunk["type"] == "result":
                    await update_task(self.session, node.id, TaskStatus.DONE, result=chunk.get("result", ""))
                    yield {"event": "task_updated", "data": {"id": node.id, "status": TaskStatus.DONE}}
                    # Resume the rest of the graph
                    async for follow_up in self.resume(node.graph_id, conversation_id):
                        yield follow_up
        except Exception as e:
            log.critical("orchestrator.resume_shell_crashed", task_id=task_id, error=str(e), exc_info=True)
            yield {"event": "error", "data": {"message": f"Critical resume failure: {str(e)}"}}
