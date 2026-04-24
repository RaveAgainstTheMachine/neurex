"""
core/agents/planner_agent.py
Decomposes a natural-language request into an ordered list of sub-tasks,
each tagged with the appropriate agent type.
"""
from __future__ import annotations
import json
import re
from typing import AsyncGenerator

import structlog

from core.agents.base_agent import BaseAgent

log = structlog.get_logger()

PLANNER_SYSTEM = """\
You are a senior software architect acting as a planning agent inside Neurex IDE.
Your ONLY job is to decompose the user's request into an ordered list of sub-tasks.

Output a JSON array (and nothing else) in this exact shape:
[
  {
    "agent":       "planner|coder|tester|researcher|reviewer",
    "title":       "Short title",
    "description": "Detailed instructions for the sub-agent"
  }
]

Rules:
- Always start with a "planner" step that writes a file/directory plan if the task
  involves creating multiple files.
- Use "coder" for any file creation, editing, or refactoring step.
- Use "tester" for any verification, linting, or test-running step.
- Use "researcher" for finding documentation, library usage, or external info.
- Use "reviewer" for checking code quality and correctness.


- Keep descriptions precise and self-contained — the sub-agent has no memory
  of sibling tasks.
- Return ONLY the JSON array. No prose, no markdown fences.
"""


class PlannerAgent(BaseAgent):
    system_prompt = PLANNER_SYSTEM
    agent_type = "planner"

    async def plan(
        self, user_message: str, conversation_id: str
    ) -> AsyncGenerator[dict, None]:
        rag = await self.rag_context(user_message, n=3)
        system = self.build_system_prompt(rag)

        messages = [
            {"role": "system", "content": system},
            {"role": "user",   "content": user_message},
        ]

        full_text = ""
        async for chunk in self.stream(messages):
            if chunk["type"] == "token":
                full_text += chunk["text"]
                yield {"type": "token", "text": chunk["text"]}
            elif chunk["type"] == "done":
                plan = self._parse_plan(full_text)
                log.info("planner.done", steps=len(plan))
                yield {"type": "result", "plan": plan}

    async def execute(self, task: dict, conversation_id: str):
        # Planner uses plan(), not execute() — satisfy ABC
        async for chunk in self.plan(task["description"], conversation_id):
            yield chunk

    # ── Internal ──────────────────────────────────────────────────────────

    def _parse_plan(self, raw: str) -> list[dict]:
        """Extract JSON plan from model output, tolerating minor formatting issues."""
        # Strip markdown fences if present
        raw = re.sub(r"```(?:json)?", "", raw).strip()
        try:
            plan = json.loads(raw)
            if isinstance(plan, list):
                return plan
        except json.JSONDecodeError:
            pass

        # Fallback: try to find the first [...] block
        match = re.search(r"\[.*\]", raw, re.DOTALL)
        if match:
            try:
                return json.loads(match.group())
            except Exception:
                pass

        log.warning("planner.parse_failed", raw=raw[:200])
        # Degenerate fallback: single coder step
        return [{"agent": "coder", "title": "Implement", "description": raw}]
