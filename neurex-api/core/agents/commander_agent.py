"""
core/agents/commander_agent.py
Specialized supervisor agent for dynamic graph re-evaluation and mid-execution planning.
"""
from __future__ import annotations
import json
import structlog
from typing import AsyncGenerator, List, Dict
from core.agents.base_agent import BaseAgent

log = structlog.get_logger()

COMMANDER_SYSTEM = """\
You are "The Commander" — the executive supervisor of the Neurex agentic swarm.
Your goal is to evaluate the current progress of a task graph and rewrite the REMAINING steps if the plan is failing or stalled.

Context:
- Project Intel: {intel}
- Current Task Progress: {progress}
- Current Error/Blocker: {error}

Rules:
1. Only provide the NEW steps for the remaining work.
2. If the current approach is fundamentally flawed, pivot to a new strategy.
3. Be decisive. Use specialized agents: coder, tester, researcher, reviewer, debater.
4. Output your plan as a JSON list of tasks.

JSON Schema:
[
  {{
    "agent_type": "coder|tester|researcher|reviewer|debater",
    "title": "Concise Task Title",
    "description": "Extremely detailed instructions for the sub-agent."
  }}
]
"""

class CommanderAgent(BaseAgent):
    agent_type = "commander"

    async def execute(self, task: dict, conversation_id: str) -> AsyncGenerator[dict, None]:
        intel = await self.mcp.call("query_project_intel", {})
        progress = task.get("progress_summary", "")
        error = task.get("current_error", "")
        
        system = COMMANDER_SYSTEM.format(intel=intel, progress=progress, error=error)
        messages = [
            {"role": "system", "content": system},
            {"role": "user",   "content": "The current plan is stalled. Re-evaluate and provide the remaining tasks to complete the original objective."}
        ]

        full_text = ""
        async for chunk in self.stream(messages):
            if chunk["type"] == "token":
                full_text += chunk["text"]
                yield {"type": "token", "text": chunk["text"]}
            elif chunk["type"] == "done":
                # Extract JSON and return as result
                try:
                    # Basic JSON extraction (looking for first [ and last ])
                    start = full_text.find("[")
                    end = full_text.rfind("]") + 1
                    if start != -1 and end != -1:
                        tasks = json.loads(full_text[start:end])
                        yield {"type": "result", "result": f"REWRITTEN_PLAN:{json.dumps(tasks)}"}
                    else:
                        yield {"type": "result", "result": full_text}
                except Exception as e:
                    log.error("commander.parse_failed", error=str(e))
                    yield {"type": "result", "result": full_text}
