"""
core/orchestrator.py
Supervisor agent. Parses a user request into a TaskGraph, then delegates
sub-tasks to specialized agents and streams status updates over a websocket.
Supports Human-in-the-Loop for plan approval.
"""

from __future__ import annotations

import asyncio
import json
import os
import uuid
from collections.abc import AsyncGenerator
from pathlib import Path

import structlog
from fastapi.encoders import jsonable_encoder
from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession

from core.agents.registry import AGENT_REGISTRY
from core.context.manager import ContextManager
from core.context.rules_parser import RulesParser
from core.infrastructure.manager import InfrastructureManager
from core.memory.hive import hive_mind
from core.task_graph import (
    TaskNode,
    TaskStatus,
    async_session,
    create_task,
    get_graph,
    update_task,
)

log = structlog.get_logger()


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
        self.last_tool_calls: dict[str, dict] = {}

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

        log.info(
            "orchestrator.summarizing_context", task_count=len(tasks), char_count=len(history_text)
        )

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
            subprocess.run(
                ["git", "-C", str(self.workspace), "rev-parse", "--is-inside-work-tree"],
                check=True,
                capture_output=True,
            )

            # Create a snapshot tag
            tag_name = f"neurex-pre-{graph_id[:8]}"
            subprocess.run(["git", "-C", str(self.workspace), "add", "."], check=True)
            # Use --allow-empty in case there are no changes
            subprocess.run(
                [
                    "git",
                    "-C",
                    str(self.workspace),
                    "commit",
                    "--allow-empty",
                    "-m",
                    f"Neurex Safe Snapshot: {graph_id}",
                ],
                capture_output=True,
            )
            # SECURITY: tag_name is constructed from graph_id (UUID), but we use '--' for safety
            subprocess.run(["git", "-C", str(self.workspace), "tag", "--", tag_name], check=True)
            log.info("safety.snapshot_created", tag=tag_name)
        except Exception as e:
            log.warning(
                "safety.snapshot_failed", error=str(e), hint="Is git initialized in the workspace?"
            )

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
            if os.getenv("NEUREX_MOCK_LLM") != "true":
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

            log.info(
                "orchestrator.using_model",
                agent="planner",
                model=model_name,
                source="user" if model else "routes",
            )

            # Consult Hive Mind for context
            memories = hive_mind.recall(user_message, limit=3)
            hive_context = (
                "\n".join([f"- {m['content']}" for m in memories])
                if memories
                else "No relevant memories found."
            )

            planner = AGENT_REGISTRY["planner"](self.rules, self.ctx, model=model_name)
            # Inject memories into the planning context
            augmented_message = (
                f"Relevant project history:\n{hive_context}\n\nUser request: {user_message}"
            )

            plan: list[dict] = []

            await update_task(self.session, planner_node.id, TaskStatus.THINKING)
            yield {
                "event": "task_updated",
                "data": {"id": planner_node.id, "status": TaskStatus.THINKING},
            }

            async for chunk in planner.plan(
                augmented_message, conversation_id, params=model_params
            ):
                if chunk["type"] == "token":
                    yield {"event": "planning_token", "data": chunk["text"]}
                elif chunk["type"] == "result":
                    plan = chunk["plan"]

            log.info("orchestrator.plan_received", steps_count=len(plan))

            if len(plan) == 1 and plan[0].get("agent") == "chat":
                # Direct conversational reply - bypass task approval
                await update_task(
                    self.session, planner_node.id, TaskStatus.DONE, result=plan[0]["description"]
                )
                yield {"event": "chat_reply", "data": plan[0]["description"]}
                yield {"event": "graph_complete", "data": {"graph_id": graph_id}}
                return

            for i, step in enumerate(plan):
                agent_type = step.get("agent", "coder")
                log.info(
                    "orchestrator.creating_subtask",
                    step=i,
                    agent=agent_type,
                    title=step.get("title"),
                )
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
                self.session, planner_node.id, TaskStatus.AWAITING_APPROVAL, result=json.dumps(plan)
            )

            from api.routes.notifications import send_notification

            send_notification(
                title="Plan Ready", body=f"Neurex has created a plan for: {planner_node.title}"
            )

            # Reload graph to send to UI
            graph = await get_graph(self.session, graph_id)
            yield {
                "event": "plan_ready",
                "data": {"graph_id": graph_id, "tasks": [jsonable_encoder(n) for n in graph]},
            }
        except Exception as e:
            log.critical("orchestrator.run_crashed", graph_id=graph_id, error=str(e), exc_info=True)
            yield {"event": "error", "data": {"message": f"Critical planning failure: {str(e)}"}}

    async def trigger_swarm_review(self, path: str, conversation_id: str):
        """Phase 45: Automated Swarm Review for Protected Paths."""
        from core.collaboration.consensus import consensus_manager

        paths_to_review = [path] if path else list(consensus_manager.proposals.keys())

        model = "mock" if os.getenv("NEUREX_MOCK_LLM") == "true" else None

        for p in paths_to_review:
            proposal = consensus_manager.get_proposal(p)
            if not proposal:
                continue

            log.info("orchestrator.swarm_review_init", path=p, model=model)

            # 1. Spawn Reviewers
            reviewer = AGENT_REGISTRY["reviewer"](self.rules, self.ctx, model=model)
            planner = AGENT_REGISTRY["planner"](self.rules, self.ctx, model=model)

            # Automate evaluation
            await consensus_manager.evaluate_mutation(
                {"path": p, "content": proposal.content, "requester": proposal.requester},
                [reviewer, planner],
                conversation_id,
            )

            log.info(
                "orchestrator.swarm_review_complete",
                path=p,
                reached=consensus_manager.get_proposal(p) is None,
            )

    async def resume(
        self,
        graph_id: str,
        conversation_id: str,
    ) -> AsyncGenerator[dict, None]:
        """Phase 4: Execution after approval using Queue isolation."""
        log.info("orchestrator.resume", graph_id=graph_id)
        queue = asyncio.Queue()

        async def _worker():
            active_node_id = None
            try:
                async with async_session() as session:
                    while True:
                        # 0. Check if graph has been cancelled
                        cancel_stmt = select(TaskNode).where(
                            TaskNode.graph_id == graph_id, TaskNode.status == TaskStatus.CANCELLED
                        )
                        cancel_result = await session.exec(cancel_stmt)
                        if cancel_result.first():
                            log.info("orchestrator.halted", graph_id=graph_id, reason="cancelled")
                            await queue.put(
                                {"event": "graph_cancelled", "data": {"graph_id": graph_id}}
                            )
                            break

                        # 1. Re-fetch tasks that are PENDING and belong to this graph
                        stmt = (
                            select(TaskNode)
                            .where(
                                TaskNode.graph_id == graph_id,
                                TaskNode.agent_type != "planner",
                                TaskNode.status == TaskStatus.PENDING,
                            )
                            .order_by(TaskNode.created_at)
                        )

                        result = await session.exec(stmt)
                        tasks = result.all()

                        if not tasks:
                            log.info("orchestrator.graph_complete", graph_id=graph_id)
                            await queue.put(
                                {"event": "graph_complete", "data": {"graph_id": graph_id}}
                            )
                            break

                        for node in tasks:
                            try:
                                active_node_id = node.id
                                if node.is_checkpoint:
                                    log.info("orchestrator.checkpoint_reached", task_id=node.id)
                                    await update_task(
                                        session,
                                        node.id,
                                        TaskStatus.AWAITING_APPROVAL,
                                        approval_reason="Breakpoint reached. Click resume to proceed.",
                                    )
                                    await queue.put(
                                        {
                                            "event": "task_updated",
                                            "data": {
                                                "id": node.id,
                                                "status": TaskStatus.AWAITING_APPROVAL,
                                                "approval_reason": "Breakpoint reached. Click resume to proceed.",
                                            },
                                        }
                                    )
                                    return

                                log.info(
                                    "orchestrator.executing_task", task_id=node.id, title=node.title
                                )
                                await update_task(session, node.id, TaskStatus.THINKING)
                                await queue.put(
                                    {
                                        "event": "task_updated",
                                        "data": {"id": node.id, "status": TaskStatus.THINKING},
                                    }
                                )

                                from core.settings.manager import settings_manager

                                # Phase 60: Resolve model via Route Map
                                role_map = {
                                    "planner": "Planning",
                                    "coder": "Coding",
                                    "tester": "Testing",
                                    "researcher": "Researching",
                                    "reviewer": "Reviewing",
                                    "debater": "Reviewing",
                                    "commander": "Planning",
                                }

                                routes = settings_manager.get("model_routes") or {}
                                target_role = role_map.get(node.agent_type, "Coding")
                                route_config = routes.get(target_role) or settings_manager.get(
                                    f"{node.agent_type}_model"
                                )

                                if isinstance(route_config, dict):
                                    model_name = route_config.get("model")
                                    model_params = route_config.get("params")
                                else:
                                    model_name = route_config
                                    model_params = None

                                if not model_params and model_name:
                                    model_params = await self.infra.resolve_model_params(model_name)
                                    if model_params == "Unknown":
                                        model_params = None

                                AgentClass = AGENT_REGISTRY.get(
                                    node.agent_type, AGENT_REGISTRY["coder"]
                                )
                                agent = AgentClass(self.rules, self.ctx, model=model_name)

                                # Gather and summarize history context
                                history_stmt = (
                                    select(TaskNode)
                                    .where(
                                        TaskNode.graph_id == graph_id,
                                        TaskNode.status == TaskStatus.DONE,
                                    )
                                    .order_by(TaskNode.created_at)
                                )
                                history_result = await session.exec(history_stmt)
                                done_tasks = history_result.all()

                                history_context = await self._summarize_history(
                                    done_tasks, model_name
                                )

                                task_payload = {
                                    "id": node.id,
                                    "title": node.title,
                                    "description": node.description,
                                    "history": history_context,
                                    "model": model_name,
                                    "params": model_params,
                                    "last_tool_call": self.last_tool_calls.get(node.id),
                                }

                                node_result = ""
                                async for chunk in agent.execute(task_payload, conversation_id):
                                    if chunk["type"] == "token":
                                        await queue.put(
                                            {
                                                "event": "token",
                                                "data": chunk["text"],
                                                "task_id": node.id,
                                            }
                                        )
                                    elif chunk["type"] == "status":
                                        await queue.put(
                                            {
                                                "event": "task_status",
                                                "data": {"id": node.id, "status": chunk["status"]},
                                            }
                                        )
                                    elif chunk["type"] == "tool_call":
                                        tool_call = chunk.get("call", {})
                                        tool_name = tool_call.get("function", {}).get("name", "")
                                        from core.mcp.client import get_tool_permission

                                        rule = await get_tool_permission(tool_name)

                                        if rule == "ask" or (
                                            self.autonomy_level == "limited"
                                            and chunk.get("tool") in ["shell", "filesystem"]
                                        ):
                                            log.info(
                                                "orchestrator.hitl_required",
                                                tool=tool_name or chunk.get("tool"),
                                            )
                                            await update_task(
                                                session, node.id, TaskStatus.AWAITING_APPROVAL
                                            )
                                            await queue.put(
                                                {
                                                    "event": "approval_required",
                                                    "data": {
                                                        "id": node.id,
                                                        "tool": tool_name
                                                        or chunk.get("tool", "unknown"),
                                                        "args": chunk.get("args")
                                                        or tool_call.get("function", {}).get(
                                                            "arguments", {}
                                                        ),
                                                    },
                                                }
                                            )
                                            self.last_tool_calls[node.id] = chunk
                                            return

                                    elif chunk["type"] == "result":
                                        node_result = chunk["result"]
                                        if (
                                            isinstance(node_result, str)
                                            and "CONSENSUS_REQUIRED" in node_result
                                        ):
                                            # Extract path if possible (this is a bit hacky, better to have it in metadata)
                                            # But for now, we trigger a broad review check
                                            log.info(
                                                "orchestrator.triggering_swarm_review",
                                                task_id=node.id,
                                            )
                                            # Background task to not block the current loop
                                            asyncio.create_task(
                                                self.trigger_swarm_review("", conversation_id)
                                            )

                                        if node.agent_type == "debater":
                                            persona = "skeptic"
                                            desc_lower = node.description.lower()
                                            title_lower = node.title.lower()
                                            if (
                                                "optimist" in desc_lower
                                                or "optimist" in title_lower
                                            ):
                                                persona = "optimist"

                                            agent_name = (
                                                "Optimist Debater"
                                                if persona == "optimist"
                                                else "Skeptic Critic"
                                            )
                                            role = "coder" if persona == "optimist" else "reviewer"

                                            from datetime import datetime

                                            await queue.put(
                                                {
                                                    "event": "debate_message",
                                                    "data": {
                                                        "id": f"debater-{node.id}",
                                                        "agent": agent_name,
                                                        "role": role,
                                                        "content": node_result,
                                                        "timestamp": datetime.now().strftime(
                                                            "%H:%M:%S"
                                                        ),
                                                    },
                                                }
                                            )

                                # Mark as DONE
                                await update_task(
                                    session, node.id, TaskStatus.DONE, result=node_result
                                )
                                await queue.put(
                                    {
                                        "event": "task_updated",
                                        "data": {"id": node.id, "status": TaskStatus.DONE},
                                    }
                                )

                                hive_mind.remember(
                                    content=f"Completed task '{node.title}' in graph {graph_id}. Result: {node_result}",
                                    metadata={
                                        "graph_id": graph_id,
                                        "agent_type": node.agent_type,
                                        "type": "task_result",
                                    },
                                    doc_id=node.id,
                                )
                                active_node_id = None

                            except Exception as e:
                                log.error("orchestrator.task_failed", task_id=node.id, error=str(e))
                                await update_task(session, node.id, TaskStatus.FAILED, error=str(e))
                                await queue.put(
                                    {
                                        "event": "task_updated",
                                        "data": {"id": node.id, "status": TaskStatus.FAILED},
                                    }
                                )
                                active_node_id = None
                                # In Phase 5, we stop the graph on any failure
                                return

                # Final cleanup
                graph = await get_graph(session, graph_id)
                await queue.put(
                    {
                        "event": "done",
                        "data": {
                            "graph_id": graph_id,
                            "tasks": [jsonable_encoder(n) for n in graph],
                        },
                    }
                )

            except Exception as e:
                log.critical(
                    "orchestrator.resume_worker_crashed",
                    graph_id=graph_id,
                    error=str(e),
                    exc_info=True,
                )
                if active_node_id:
                    try:
                        async with async_session() as session:
                            await update_task(
                                session,
                                active_node_id,
                                TaskStatus.FAILED,
                                error=f"Orchestrator crash: {str(e)}",
                            )
                    except Exception as update_err:
                        log.error("orchestrator.crash_update_failed", error=str(update_err))
                await queue.put(
                    {"event": "error", "data": {"message": f"Execution failure: {str(e)}"}}
                )
            finally:
                await queue.put(None)

        asyncio.create_task(_worker())

        while True:
            event = await queue.get()
            if event is None:
                break
            yield event

    async def resume_shell(
        self,
        task_id: str,
        approved: bool,
        conversation_id: str,
    ) -> AsyncGenerator[dict, None]:
        """Phase 4: Resuming a task after a shell approval using Queue isolation."""
        queue = asyncio.Queue()

        async def _worker():
            try:
                async with async_session() as session:
                    stmt = select(TaskNode).where(TaskNode.id == task_id)
                    res = await session.exec(stmt)
                    node = res.first()
                    if not node:
                        return

                    log.info("orchestrator.resume_shell_worker", task_id=task_id, approved=approved)

                    if not approved:
                        await update_task(
                            session, node.id, TaskStatus.FAILED, error="User denied shell command"
                        )
                        await queue.put(
                            {
                                "event": "task_updated",
                                "data": {"id": node.id, "status": TaskStatus.FAILED},
                            }
                        )
                        return

                    node.result = ""
                    session.add(node)
                    await session.commit()

                    from core.settings.manager import settings_manager

                    settings_key = f"{node.agent_type}_model"
                    model_name = settings_manager.get(settings_key)

                    model_params = await self.infra.resolve_model_params(model_name)
                    if model_params == "Unknown":
                        model_params = None

                    AgentClass = AGENT_REGISTRY.get(node.agent_type, AGENT_REGISTRY["coder"])
                    agent = AgentClass(self.rules, self.ctx, model=model_name)

                    step = {
                        "id": node.id,
                        "description": f"{node.description}\n[USER APPROVED SHELL EXECUTION]",
                        "title": node.title,
                        "params": model_params,
                        "last_tool_call": self.last_tool_calls.get(node.id),
                    }

                    first_tool_call = True
                    async for chunk in agent.execute(step, conversation_id):
                        if chunk["type"] == "status":
                            await update_task(session, node.id, chunk["status"])
                            await queue.put(
                                    {
                                        "event": "task_updated",
                                        "data": {"id": node.id, "status": chunk["status"]},
                                    }
                                )
                        elif chunk["type"] == "token":
                            await queue.put({"event": "token", "data": chunk["text"]})
                        elif chunk["type"] == "tool_call":
                            tool_call = chunk.get("call", {})
                            tool_name = tool_call.get("function", {}).get("name", "")

                            if first_tool_call:
                                first_tool_call = False
                                log.info("orchestrator.resume_shell.executing_approved_tool", tool=tool_name)
                                await queue.put({"event": "tool_call", "data": chunk})
                                continue

                            from core.mcp.client import get_tool_permission

                            rule = await get_tool_permission(tool_name)

                            if rule == "ask" or (
                                self.autonomy_level == "limited"
                                and chunk.get("tool") in ["shell", "filesystem"]
                            ):
                                log.info(
                                    "orchestrator.resume_shell.hitl_required",
                                    tool=tool_name or chunk.get("tool"),
                                )
                                await update_task(session, node.id, TaskStatus.AWAITING_APPROVAL)
                                await queue.put(
                                    {
                                        "event": "approval_required",
                                        "data": {
                                            "id": node.id,
                                            "tool": tool_name or chunk.get("tool", "unknown"),
                                            "args": chunk.get("args")
                                            or tool_call.get("function", {}).get("arguments", {}),
                                        },
                                    }
                                )
                                self.last_tool_calls[node.id] = chunk
                                return  # Pause worker for approval

                            # For non-sensitive tools, just log observability event
                            await queue.put({"event": "tool_call", "data": chunk})

                        elif chunk["type"] == "result":
                            node_result = chunk.get("result", "")
                            if isinstance(node_result, str) and "CONSENSUS_REQUIRED" in node_result:
                                log.info(
                                    "orchestrator.resume_shell.triggering_swarm_review",
                                    task_id=node.id,
                                )
                                asyncio.create_task(self.trigger_swarm_review("", conversation_id))

                            await update_task(session, node.id, TaskStatus.DONE, result=node_result)
                            await queue.put(
                                {
                                    "event": "task_updated",
                                    "data": {"id": node.id, "status": TaskStatus.DONE},
                                }
                            )
                            # Resume the rest of the graph
                            async for follow_up in self.resume(node.graph_id, conversation_id):
                                await queue.put(follow_up)

            except Exception as e:
                log.critical(
                    "orchestrator.resume_shell_worker_crashed",
                    task_id=task_id,
                    error=str(e),
                    exc_info=True,
                )
                await queue.put(
                    {"event": "error", "data": {"message": f"Resume failure: {str(e)}"}}
                )
            finally:
                await queue.put(None)  # End of stream

        asyncio.create_task(_worker())

        while True:
            event = await queue.get()
            if event is None:
                break
            yield event

    async def execute_inline_edit(
        self,
        path: str,
        prompt: str,
        selection: str,
        range_coords: dict | None,
        task_id: str,
        conversation_id: str,
    ) -> AsyncGenerator[dict, None]:
        """Fast-path inline edit execution bypassing the high-level planner graph."""
        log.info("orchestrator.inline_edit", path=path, task_id=task_id)

        file_abs_path = self.workspace / path
        if not file_abs_path.exists():
            yield {"event": "error", "data": f"File does not exist: {path}"}
            return

        try:
            with open(file_abs_path, encoding="utf-8") as f:
                original_content = f.read()
        except Exception as e:
            yield {"event": "error", "data": f"Failed to read file: {str(e)}"}
            return

        import time

        from core.collaboration.presence import presence_manager

        agent_id = "Agent [Neurex Coder]"

        # Initialize presence for agent
        if conversation_id not in presence_manager.presence_state:
            presence_manager.presence_state[conversation_id] = {}
        presence_manager.presence_state[conversation_id][agent_id] = {
            "user_id": agent_id,
            "cursor": {"line": 1, "ch": 1},
            "active_file": path,
            "status": "online",
            "last_ping": time.time(),
        }
        await presence_manager.broadcast(
            conversation_id,
            {
                "event": "presence_update",
                "data": list(presence_manager.presence_state[conversation_id].values()),
            },
        )

        try:
            # Handle Mock LLM baseline testing
            if os.getenv("NEUREX_MOCK_LLM") == "true":
                # Just do a mock replacement in the selected text
                mock_modified = original_content
                if selection and selection in original_content:
                    mock_modified = original_content.replace(
                        selection, f"{selection}\n# Refactored by Mock AI: {prompt}"
                    )
                else:
                    mock_modified = f"{original_content}\n# Refactored by Mock AI: {prompt}"

                yield {
                    "event": "task_updated",
                    "data": {"id": task_id, "status": "THINKING"},
                }
                # Simulate smooth, high-frequency typing motion in Mock LLM too!
                lines = mock_modified.split("\n")
                for i in range(1, len(lines) + 1):
                    presence_manager.presence_state[conversation_id][agent_id].update(
                        {
                            "cursor": {"line": i, "ch": len(lines[i - 1]) + 1},
                            "active_file": path,
                            "last_ping": time.time(),
                        }
                    )
                    await presence_manager.broadcast(
                        conversation_id,
                        {
                            "event": "presence_update",
                            "data": list(presence_manager.presence_state[conversation_id].values()),
                        },
                    )
                    await asyncio.sleep(0.016)  # ~60Hz typing sleep

                yield {
                    "event": "task_updated",
                    "data": {"id": task_id, "status": "DONE"},
                }
                yield {
                    "event": "inline_edit_diff",
                    "data": {
                        "path": path,
                        "original": original_content,
                        "modified": mock_modified,
                        "taskId": task_id,
                    },
                }
                return

            # 1. Resolve model via routes
            from core.settings.manager import settings_manager

            routes = settings_manager.get("model_routes") or {}
            model_name = routes.get("Coding") or settings_manager.get("coder_model")
            if isinstance(model_name, dict):
                model_params = model_name.get("params")
                model_name = model_name.get("model")
            else:
                model_params = await self.infra.resolve_model_params(model_name)
                if model_params == "Unknown":
                    model_params = None

            # 2. Construct targeted system and user prompts
            system_prompt = (
                "You are a precise code refactoring assistant inside Neurex IDE.\n"
                "You will be given the entire content of a file, the user's selected text in that file, and a prompt instruction.\n"
                "Your task is to modify the code inside the file based on the instruction.\n"
                "Return the COMPLETE new contents of the entire file. Do NOT output a diff or partial replacement.\n"
                "Return ONLY the raw contents of the modified file. Do NOT wrap it in markdown block quotes (such as ```python or ```) or prefix it with any intro or explanation. Just return the raw file content."
            )

            user_prompt = (
                f"FILE PATH: {path}\n\n"
                f"=== CURRENT FULL FILE CONTENT ===\n"
                f"{original_content}\n"
                f"=================================\n\n"
                f"=== SELECTED RANGE TEXT ===\n"
                f"{selection or ''}\n"
                f"============================\n\n"
                f"INSTRUCTION: {prompt}\n\n"
                f"Apply the instruction and output the complete, raw content of the modified file."
            )

            messages = [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ]

            from core.agents.base_agent import BaseAgent

            class InlineHelperAgent(BaseAgent):
                system_prompt = "You are a precise refactoring assistant."
                agent_type = "inline_helper"

                async def execute(
                    self, task: dict, conversation_id: str
                ) -> AsyncGenerator[dict, None]:
                    pass

            agent = InlineHelperAgent(self.rules, self.ctx, model=model_name)

            yield {
                "event": "task_updated",
                "data": {"id": task_id, "status": "THINKING"},
            }

            modified_content_chunks = []
            last_update_time = 0.0
            async for chunk in agent.stream(messages, params=model_params):
                if chunk["type"] == "token":
                    token = chunk["text"]
                    modified_content_chunks.append(token)
                    yield {"event": "token", "data": token, "task_id": task_id}

                    # Throttled 60Hz Telemetry Stream
                    current_time = time.time()
                    if current_time - last_update_time >= (1.0 / 60.0):
                        last_update_time = current_time
                        accumulated = "".join(modified_content_chunks)
                        lines = accumulated.split("\n")
                        line_num = len(lines)
                        col_num = len(lines[-1]) + 1

                        presence_manager.presence_state[conversation_id][agent_id].update(
                            {
                                "cursor": {"line": line_num, "ch": col_num},
                                "active_file": path,
                                "last_ping": time.time(),
                            }
                        )
                        await presence_manager.broadcast(
                            conversation_id,
                            {
                                "event": "presence_update",
                                "data": list(
                                    presence_manager.presence_state[conversation_id].values()
                                ),
                            },
                        )
                elif chunk["type"] == "done":
                    break

            full_modified = "".join(modified_content_chunks)

            # Strip markdown fences if any
            full_modified = full_modified.strip()
            if full_modified.startswith("```"):
                lines = full_modified.splitlines()
                if len(lines) >= 2:
                    if lines[0].startswith("```"):
                        lines = lines[1:]
                    if lines[-1].strip() == "```":
                        lines = lines[:-1]
                    full_modified = "\n".join(lines)

            yield {
                "event": "task_updated",
                "data": {"id": task_id, "status": "DONE"},
            }

            yield {
                "event": "inline_edit_diff",
                "data": {
                    "path": path,
                    "original": original_content,
                    "modified": full_modified,
                    "taskId": task_id,
                },
            }
        finally:
            # Clean up the agent's presence cursor update when generation completes or crashes
            if (
                conversation_id in presence_manager.presence_state
                and agent_id in presence_manager.presence_state[conversation_id]
            ):
                del presence_manager.presence_state[conversation_id][agent_id]
                await presence_manager.broadcast(
                    conversation_id,
                    {
                        "event": "presence_update",
                        "data": list(presence_manager.presence_state[conversation_id].values()),
                    },
                )
