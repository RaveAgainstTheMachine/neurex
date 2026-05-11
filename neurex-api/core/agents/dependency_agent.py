"""
core/agents/dependency_agent.py
Specialized agent for auditing and upgrading project dependencies.
"""

from __future__ import annotations

from collections.abc import AsyncGenerator

import structlog

from core.agents.base_agent import BaseAgent

log = structlog.get_logger()

DEPENDENCY_SYSTEM = """\
You are a dependency hardening specialist for Neurex. 
Your goal is to ensure project dependencies are up-to-date, secure, and compatible.

When executing a task:
1. Audit the environment (e.g., `pip list --outdated` or `npm outdated`).
2. Propose upgrades that minimize breaking changes.
3. Apply upgrades and run verification steps.

You have access to shell tools to check versions.
Always summarize the risk level of any proposed upgrade.
"""


class DependencyAgent(BaseAgent):
    system_prompt = DEPENDENCY_SYSTEM
    agent_type = "dependency"

    async def execute(self, task: dict, conversation_id: str) -> AsyncGenerator[dict, None]:
        """Execute a dependency audit or upgrade task."""
        log.info("dependency_agent.execute", task=task.get("title"))

        prompt = f"Context: {task.get('history', '')}\nTask: {task.get('description', '')}"
        messages = [
            {"role": "system", "content": await self.build_system_prompt(conversation_id)},
            {"role": "user", "content": prompt},
        ]

        full_text = ""
        async for chunk in self.stream(messages, params=task.get("params")):
            if chunk["type"] == "token":
                full_text += chunk["text"]
                yield chunk
            elif chunk["type"] == "tool_call":
                # Intercept or pass through tool calls
                result = await self.dispatch_tool(chunk["call"], conversation_id)
                messages.append({"role": "assistant", "tool_calls": [chunk["call"]]})
                messages.append(
                    {"role": "tool", "tool_call_id": chunk["call"]["id"], "content": result}
                )
                yield chunk
            elif chunk["type"] == "done":
                yield {"type": "result", "result": full_text}
                break
