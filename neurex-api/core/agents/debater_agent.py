"""
core/agents/debater_agent.py
Specialized agent for architectural peer-review and strategy refinement.
"""

from __future__ import annotations

from collections.abc import AsyncGenerator

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
        intel = await self.mcp.call("query_project_intel", {}, conversation_id=conversation_id)

        system_base = DEBATER_SYSTEM.format(persona=persona, intel=intel)
        if hasattr(self.ctx, "debate_verdicts") and conversation_id in self.ctx.debate_verdicts:
            verdict = self.ctx.debate_verdicts[conversation_id]
            system_base += f'\n\n🚨 ARCHITECT JUDGE DIRECTIVE:\nThe Architect Judge (User) has issued a verdict to steer this debate:\n"{verdict}"\nYou MUST adapt your critique/argument to align with, address, or incorporate this directive directly.'

        system = await self.build_system_prompt(conversation_id, system_base)
        history = task.get("history", "")
        user_content = f"Critique this plan: {task['description']}"
        if history:
            if isinstance(history, str):
                user_content = f"Prior task execution history:\n{history}\n\nTask to execute:\n{user_content}"
            elif isinstance(history, list):
                history_text = "\n".join([
                    f"Role: {m.get('role')}\nContent: {m.get('content')}"
                    for m in history if isinstance(m, dict)
                ])
                if history_text:
                    user_content = f"Prior task execution history:\n{history_text}\n\nTask to execute:\n{user_content}"

        messages = [
            {"role": "system", "content": system},
            {"role": "user", "content": user_content},
        ]

        full_text = ""
        params = task.get("params")
        async for chunk in self.stream(messages, params=params):
            if chunk["type"] == "token":
                full_text += chunk["text"]
                yield {"type": "token", "text": chunk["text"]}
            elif chunk["type"] == "done":
                yield {"type": "result", "result": full_text}
