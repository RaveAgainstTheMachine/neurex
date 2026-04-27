"""
core/agents/debater_agent.py
Specialized agent for architectural peer-review and strategy refinement.
"""
from __future__ import annotations
from typing import AsyncGenerator
import structlog
from core.agents.base_agent import BaseAgent

log = structlog.get_logger()

DEBATER_SYSTEM = """\
You are an expert software architect participating in a technical debate.
Your goal is to critique or defend a proposed technical plan.

PERSONA: {persona}

Context:
- Project Architecture: {intel}

Rules:
1. Be specific. Reference file paths and design patterns.
2. If you are the SKEPTIC, look for:
   - Performance bottlenecks.
   - Security vulnerabilities.
   - Technical debt or anti-patterns.
3. If you are the OPTIMIST, look for:
   - Developer velocity improvements.
   - Scalability benefits.
   - Modern best practices.

Output your argument as a concise technical critique (max 300 words).
"""

class DebaterAgent(BaseAgent):
    agent_type = "debater"

    async def execute(self, task: dict, conversation_id: str) -> AsyncGenerator[dict, None]:
        persona = task.get("persona", "skeptic")
        intel = await self.mcp.call("query_project_intel", {})
        
        system = DEBATER_SYSTEM.format(persona=persona, intel=intel)
        messages = [
            {"role": "system", "content": system},
            {"role": "user",   "content": f"Critique this plan: {task['description']}"}
        ]

        full_text = ""
        async for chunk in self.stream(messages):
            if chunk["type"] == "token":
                full_text += chunk["text"]
                yield {"type": "token", "text": chunk["text"]}
            elif chunk["type"] == "done":
                yield {"type": "result", "result": full_text}
