"""
core/agents/tester_agent.py
Runs tests, linters, and type-checkers inside a sandboxed Docker container
via the MCP terminal tool. Never executes on the host directly.
"""
from __future__ import annotations
from typing import AsyncGenerator
import structlog

from core.agents.base_agent import BaseAgent
from core.task_graph import TaskStatus

log = structlog.get_logger()

TESTER_TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "run_command",
            "description": (
                "Run a shell command inside the sandboxed workspace container. "
                "Use for: pytest, ruff, mypy, eslint, tsc, etc. "
                "Output is captured and returned. Max runtime 60s."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "command": {"type": "string", "description": "The shell command to run"},
                    "cwd":     {"type": "string", "description": "Working directory (relative to workspace root, default '.')"},
                },
                "required": ["command"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "read_file",
            "description": "Read a file to understand context before running tests.",
            "parameters": {
                "type": "object",
                "properties": {
                    "path": {"type": "string"}
                },
                "required": ["path"],
            },
        },
    },
]

TESTER_SYSTEM = """\
You are a QA engineer inside Neurex IDE with access to a sandboxed shell.
Your job is to verify that the code written by the Coder agent is correct.
Steps:
1. Read relevant files to understand what was written.
2. Run appropriate checks: linters (ruff, eslint), type-checkers (mypy, tsc), tests (pytest, jest).
3. If checks fail, report the exact error output. Do NOT attempt to fix code — that is the Coder's job.
4. If all checks pass, confirm with a brief summary.
Always prefer running existing test suites over writing new tests unless explicitly asked.
"""


class TesterAgent(BaseAgent):
    system_prompt = TESTER_SYSTEM
    agent_type = "tester"

    async def execute(
        self, task: dict, conversation_id: str
    ) -> AsyncGenerator[dict, None]:
        description = task.get("description", "")
        system = await self.build_system_prompt(conversation_id)

        messages = [
            {"role": "system", "content": system},
            {"role": "user",   "content": description},
        ]

        yield {"type": "status", "status": TaskStatus.TESTING}

        params = task.get("params")
        max_rounds = 5
        for _ in range(max_rounds):
            async for chunk in self.stream(messages, tools=TESTER_TOOLS, params=params):
                if chunk["type"] == "token":
                    yield {"type": "token", "text": chunk["text"]}

                elif chunk["type"] == "tool_call":
                    yield {"type": "tool_call", "call": chunk["call"]}
                    tool_result = await self.dispatch_tool(chunk["call"], conversation_id)
                    messages.append({
                        "role": "assistant",
                        "content": None,
                        "tool_calls": [chunk["call"]],
                    })
                    messages.append({"role": "tool", "content": tool_result})

                elif chunk["type"] == "done":
                    if not any(m.get("role") == "tool" for m in messages[-2:]):
                        yield {"type": "result", "result": chunk["full_text"]}
                        return

        yield {"type": "result", "result": "Max rounds reached."}
