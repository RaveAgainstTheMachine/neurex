"""
core/agents/reviewer_agent.py
Reviewer agent. Critiques code for quality, security, and adherence to rules.
"""
from __future__ import annotations

from collections.abc import AsyncGenerator

import structlog

from core.agents.base_agent import BaseAgent
from core.task_graph import TaskStatus

log = structlog.get_logger()

REVIEWER_SYSTEM = """\
You are a senior code reviewer inside Neurex IDE.
Your goal is to ensure all code changes are correct, efficient, and follow the project rules.

Review criteria:
1. Logic: Does it actually solve the user's problem?
2. Security: Are there path traversals or dangerous shell commands?
3. Quality: Are there type hints? Is logging structured?
4. Rules: Does it follow .neurexrules?

If the code is acceptable, start your response with 'APPROVE'.
Otherwise, provide specific feedback on what needs fixing.
"""

class ReviewerAgent(BaseAgent):
    """Agent specialized in code review and quality assurance."""
    
    system_prompt: str = REVIEWER_SYSTEM
    agent_type: str = "reviewer"

    def execute(
        self, task: dict, conversation_id: str
    ) -> AsyncGenerator[dict, None]:
        description = task.get("description", "")
        # Reviewer needs heavy context of what was just written
        rag = await self.rag_context(description, n=10)
        system = await self.build_system_prompt(conversation_id, rag)

        messages = [
            {"role": "system",  "content": system},
            {"role": "user",    "content": f"Review the following task implementation: {description}"},
        ]

        yield {"type": "status", "status": TaskStatus.TESTING}
        log.info("agent.reviewer.start", task=task.get("title"), conversation_id=conversation_id)

        params = task.get("params")
        full_text = ""
        async for chunk in self.stream(messages, params=params):
            if chunk["type"] == "token":
                full_text += chunk["text"]
                yield {"type": "token", "text": chunk["text"]}
            elif chunk["type"] == "done":
                log.info("agent.reviewer.done", task=task.get("title"))
                yield {"type": "result", "result": full_text}
