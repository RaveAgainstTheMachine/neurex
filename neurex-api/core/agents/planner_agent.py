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
    "agent":       "planner|coder|tester|researcher|reviewer|swarm",
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
- Use "debater" with `persona: "optimist"` or `persona: "skeptic"` to vet complex architectural decisions.

- SWARM RULE: If a task involves refactoring more than 10 files or implementing a cross-cutting feature across multiple modules, use the "swarm" agent. The swarm agent will decompose the task further and distribute it across the Mesh.

- INTELLIGENCE RULE: If you detect that you are in a fresh workspace or lack architectural context, your FIRST step must be "Architectural Discovery" using the `synthesize_project_intel` tool.
- SELF-EVOLUTION RULE: If the request involves project maintenance, health checks, or evolution, include a step for `audit_codebase_health` to identify drifts or anomalies before implementation.

- DEBATE RULE: For high-risk refactors or core module changes, include two "debater" steps (optimist/skeptic pair) to critique the approach before coding starts.

- Keep descriptions precise and self-contained — the sub-agent has no memory
  of sibling tasks.
- CONVERSATION RULE: If the user is simply greeting you, making small talk, or asking a meta-question about Neurex that doesn't require a technical task (e.g., "hi", "how are you", "who are you"), do NOT output a JSON array. Instead, reply directly in natural language.
- Return ONLY the JSON array for technical tasks. No prose, no markdown fences.

"""


class PlannerAgent(BaseAgent):
    system_prompt = PLANNER_SYSTEM
    agent_type = "planner"

    async def plan(
        self, user_message: str, conversation_id: str, params: str | None = None
    ) -> AsyncGenerator[dict, None]:
        rag = await self.rag_context(user_message, n=3)
        system = await self.build_system_prompt(conversation_id, rag)

        messages = [
            {"role": "system", "content": system},
            {"role": "user",   "content": user_message},
        ]

        full_text = ""
        async for chunk in self.stream(messages, params=params):
            if chunk["type"] == "token":
                full_text += chunk["text"]
                yield {"type": "token", "text": chunk["text"]}
            elif chunk["type"] == "done":
                # Check for project intelligence
                import os
                ws = os.getenv("WORKSPACE_PATH", "/workspace")
                intel_path = os.path.join(ws, ".neurex", "intel.json")
                needs_intel = not os.path.exists(intel_path)

                plan = self._parse_plan(full_text)
                
                if needs_intel:
                    # Inject discovery as the first step
                    discovery_step = {
                        "agent": "planner",
                        "title": "Architectural Discovery",
                        "description": "Synthesize project intelligence to establish the architectural brain for this workspace."
                    }
                    # Avoid double discovery if the model already added it
                    if not any("Discovery" in s.get("title", "") for s in plan):
                        plan.insert(0, discovery_step)

                log.info("planner.done", steps=len(plan), needs_intel=needs_intel)
                yield {"type": "result", "plan": plan}

    async def execute(self, task: dict, conversation_id: str):
        # Planner uses plan(), not execute() — satisfy ABC
        params = task.get("params")
        async for chunk in self.plan(task["description"], conversation_id, params=params):
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

        log.info("planner.direct_reply_detected", length=len(raw))
        # Use "chat" agent for direct conversational replies
        return [{"agent": "chat", "title": "Reply", "description": raw}]
