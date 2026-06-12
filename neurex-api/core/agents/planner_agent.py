"""
core/agents/planner_agent.py
Decomposes a natural-language request into an ordered list of sub-tasks,
each tagged with the appropriate agent type.
"""

from __future__ import annotations

import json
import re
from collections.abc import AsyncGenerator

import structlog

from core.agents.base_agent import BaseAgent

log = structlog.get_logger()

PLANNER_SYSTEM = """\
You are the planning agent for Neurex IDE — a senior software architect.
Your ONLY output is a valid JSON array of sub-tasks. Nothing else.

JSON shape (exactly):
[
  {
    "agent":       "coder|tester|researcher|reviewer|swarm|planner",
    "title":       "Short imperative title",
    "description": "EXTREMELY DETAILED step-by-step instructions for the sub-agent. MUST NOT BE EMPTY OR REPEAT THE TITLE."
  }
]

AGENT SELECTION:
- coder       → create, edit, refactor, delete any file (MUST use for creating/modifying/implementing code or files)
- tester      → run tests, lint, validate, verify outputs
- researcher  → fetch docs, investigate libraries, gather context
- reviewer    → code-quality audit, correctness check
- swarm       → >10 files or cross-cutting concern spanning many modules
- planner     → write file/directory layout plan before multi-file creation

SPECIAL RULES:
- AGENTIC EXECUTION: Neurex is an agentic IDE. The sub-tasks you output will be executed physically in the workspace by other agents. Do NOT output a "chat" agent step to explain how to write code. You MUST output "coder" steps to write, edit, and create the files.
- INTELLIGENCE: If no `.neurex/intel.json` exists or workspace seems fresh, first step must be a planner step titled "Architectural Discovery".
- EMPTY WORKSPACE: If the workspace is empty and the user does not specify a tech stack (e.g., language, framework), you MUST explicitly declare a sensible modern tech stack (e.g., Python/FastAPI + React/TS) in the 'coder' task descriptions so they know what to build.
- DEBATE: For high-risk architectural changes, add two debater steps (optimist + skeptic) before coder steps.
- SWARM: If task touches >10 files, use swarm agent.
- SELF-CONTAINED: Each description must contain ALL info the sub-agent needs. Sub-agents have NO memory of sibling tasks.

CONVERSATION EXCEPTION (RARE):
IF AND ONLY IF the user message is a pure greeting ("hi", "hello", "who are you?") or a generic worldview question completely unrelated to the project, output:
[{"agent": "chat", "title": "Reply", "description": "<your natural language answer here>"}]

For ALL other requests — including "create X", "make a game", "write Y", "explain code Z", "how does X work?", "find Y", or "implement W" — you MUST output real actionable sub-tasks (like researcher, coder, tester) to write, investigate, or verify code.
NEVER answer technical or codebase questions directly with a "chat" agent. You MUST spawn a "researcher" agent to investigate the codebase first using tools.

OUTPUT: Raw JSON array only. No markdown. No backticks. No explanation before or after.
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
            {
                "role": "user",
                "content": (
                    f"USER REQUEST: {user_message}\n\n"
                    f"CRITICAL REMINDER: You are the PLANNER. You must NOT write code. "
                    f"You must ONLY output a valid JSON array of tasks for OTHER agents (like 'coder', 'researcher') to execute. "
                    f"Output ONLY JSON. No markdown fences. No code.\n"
                    f"CRITICAL: Every task MUST have an 'agent', 'title', and 'description' field. NEVER omit the description field! The description must contain the full instructions for the agent."
                )
            },
        ]

        async for chunk in self.stream(messages, params=params):
            if chunk["type"] == "token":
                yield {"type": "token", "text": chunk["text"]}
            elif chunk["type"] == "done":
                # Check for project intelligence
                import os

                from core.mcp.tools.filesystem import get_workspace_root
                
                raw_full_text = chunk.get("full_text", "")

                ws = str(get_workspace_root())
                intel_path = os.path.join(ws, ".neurex", "intel.json")
                needs_intel = not os.path.exists(intel_path)

                plan = self._parse_plan(raw_full_text, user_message)

                if needs_intel:
                    # Inject discovery as the first step
                    discovery_step = {
                        "agent": "planner",
                        "title": "Architectural Discovery",
                        "description": "Synthesize project intelligence to establish the architectural brain for this workspace.",
                    }
                    # Avoid double discovery if the model already added it
                    if not any("Discovery" in s.get("title", "") for s in plan):
                        plan.insert(0, discovery_step)

                non_planner_steps = [s for s in plan if s.get("agent") != "planner"]
                if len(non_planner_steps) >= 3:
                    log.info("planner.hyperplan_activated", steps=len(non_planner_steps))
                    yield {"type": "status", "status": "hyperplan_analyzing"}
                    from core.harness.hyperplan import HyperPlan
                    hp = HyperPlan(self)
                    try:
                        blueprint = await hp.generate_blueprint(user_message)
                        if "tasks" in blueprint and isinstance(blueprint["tasks"], list):
                            plan = blueprint["tasks"]
                            # Re-inject discovery if needed
                            if needs_intel and not any("Discovery" in s.get("title", "") for s in plan):
                                plan.insert(0, discovery_step)
                    except Exception as e:
                        log.warning("planner.hyperplan_failed", error=str(e))

                log.info("planner.done", steps=len(plan), needs_intel=needs_intel)
                yield {"type": "result", "plan": plan, "result": json.dumps(plan)}

    async def execute(self, task: dict, conversation_id: str):
        # Planner uses plan(), not execute() — satisfy ABC
        params = task.get("params")
        async for chunk in self.plan(task["description"], conversation_id, params=params):
            yield chunk

    # ── Internal ──────────────────────────────────────────────────────────

    def _parse_plan(self, raw: str, user_message: str) -> list[dict]:
        """Extract JSON plan from model output, tolerating minor formatting issues."""
        # Strip markdown fences
        cleaned = re.sub(r"```(?:json)?", "", raw).strip().rstrip("`")

        # Attempt 1: direct parse
        try:
            plan = json.loads(cleaned)
            if isinstance(plan, list) and plan:
                return plan
        except json.JSONDecodeError:
            pass

        # Attempt 2: find first [...] block (handles prose prefix/suffix)
        match = re.search(r"(\[\s*\{.*?\}\s*\])", cleaned, re.DOTALL)
        if match:
            try:
                plan = json.loads(match.group(1))
                if isinstance(plan, list) and plan:
                    log.info("planner.extracted_json_from_prose", length=len(raw))
                    return plan
            except Exception:
                pass

        # Attempt 3: find first { ... } and check if it's a single task or contains an array
        match2 = re.search(r"(\{.*\})", cleaned, re.DOTALL)
        if match2:
            try:
                obj = json.loads(match2.group(1))
                if isinstance(obj, dict):
                    # Check if it contains a list of tasks
                    for key, val in obj.items():
                        if isinstance(val, list) and len(val) > 0 and isinstance(val[0], dict) and "agent" in val[0]:
                            log.info("planner.extracted_array_from_obj_wrapper", length=len(raw))
                            return val
                    # Or if it's a single task
                    if "agent" in obj:
                        log.info("planner.extracted_single_obj", length=len(raw))
                        return [obj]
            except Exception:
                pass

        log.warning("planner.parse_failed_chat_fallback", length=len(raw), preview=raw[:200])
        # Last resort: fallback to a generic coder step instead of a chat to force agentic behavior if the user asked to do something.
        # But if it looks like a pure chat reply, fallback to chat.
        user_lower = user_message.lower()
        agent_type = "coder" if any(kw in user_lower for kw in ["create", "build", "write", "fix", "implement", "add", "make", "game", "app"]) else "chat"
        return [{"agent": agent_type, "title": "Execution", "description": raw}]
