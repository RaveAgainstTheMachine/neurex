"""
core/agents/swarm_agent.py
Specialized agent that handles distributed swarm execution.
Acts as the interface between the Orchestrator and the SwarmManager.
"""
from __future__ import annotations
from typing import AsyncGenerator
import structlog
from core.agents.base_agent import BaseAgent
from core.agents.swarm_manager import swarm_manager
from core.task_graph import TaskNode

log = structlog.get_logger()

class SwarmAgent(BaseAgent):
    agent_type = "swarm"

    async def execute(self, task: dict, conversation_id: str) -> AsyncGenerator[dict, None]:
        """
        Decomposes the high-level swarm task and orchestrates execution across peers.
        """
        log.info("swarm_agent.executing", title=task["title"])
        yield {"type": "status", "status": "planning_swarm"}
        
        # 1. Self-Decomposition: The SwarmAgent uses its own LLM to break the task down
        # into sub-tasks that the SwarmManager can dispatch.
        plan_prompt = f"""
        You are a Swarm Leader. Decompose this massive task into a list of parallelizable sub-tasks.
        Intelligently assign a 'model' to each task:
        - Use 'Neurex Brain (Logic)' (qwen2.5-coder:32b) for complex logical changes.
        - Use 'Neurex Brain (Fast)' (qwen2.5-coder:7b) for boilerplate or simple tasks.
        - Use 'Neurex Brain (Standard)' (qwen2.5-coder:14b) for standard coding.
        
        Task: {task['title']}
        Description: {task['description']}
        
        Return a JSON array of sub-tasks:
        [
          {{"title": "...", "description": "...", "files": ["path/to/file1", ...], "model": "..."}}
        ]
        """
        
        sub_plan = []
        async for chunk in self.stream([{"role": "user", "content": plan_prompt}]):
            if chunk["type"] == "done":
                import json
                import re
                raw = re.sub(r"```(?:json)?", "", chunk["full_text"]).strip()
                try:
                    sub_plan = json.loads(raw)
                except:
                    # Fallback
                    sub_plan = [{"title": task["title"], "description": task["description"]}]
        
        yield {"type": "token", "text": f"Swarm initialized with {len(sub_plan)} agents...\n"}
        
        # 2. Handoff to SwarmManager for Mesh dispatch
        # We need a TaskNode reference, but 'task' dict is just a payload.
        # We'll create a dummy context for the manager.
        from core.task_graph import TaskNode
        dummy_parent = TaskNode(title=task["title"], description=task["description"], agent_type="swarm")
        
        swarm_id = await swarm_manager.initiate_swarm(dummy_parent, sub_plan)
        
        yield {"type": "status", "status": "swarm_executing"}
        
        # Wait for completion
        while swarm_manager.active_swarms[swarm_id].status != "completed":
            await asyncio.sleep(1)
            
        swarm = swarm_manager.active_swarms[swarm_id]
        summary = "\n".join([f"- {res['summary']}" for res in swarm.results.values()])
        
        yield {"type": "result", "result": f"Swarm {swarm_id} completed successfully.\n\nSummary of work:\n{summary}"}

import asyncio # Needed for the sleep loop
