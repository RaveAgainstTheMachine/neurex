"""
core/agents/tester_agent.py
Runs tests, linters, and type-checkers inside a sandboxed Docker container
via the MCP terminal tool. Never executes on the host directly.
"""

from __future__ import annotations

from collections.abc import AsyncGenerator

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
                    "cwd": {
                        "type": "string",
                        "description": "Working directory (relative to workspace root, default '.')",
                    },
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
                "properties": {"path": {"type": "string"}},
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

CRITICAL: Do NOT thank other agents, thank the user, or thank yourself. Do not use conversational filler, greetings, or politeness (e.g., 'Thank you for the plan', 'Starting task now', 'Great job'). Keep your thoughts and outputs strictly technical, objective, and direct.
"""


class TesterAgent(BaseAgent):
    system_prompt = TESTER_SYSTEM
    agent_type = "tester"

    async def execute(self, task: dict, conversation_id: str) -> AsyncGenerator[dict, None]:
        description = task.get("description", "")
        system = await self.build_system_prompt(conversation_id)

        # Inject prior agent context so tester can verify what was produced
        history = task.get("history", "")
        context = task.get("context", "")

        user_content = description
        if context:
            user_content = f"Relevant code context:\n{context}\n\n{user_content}"

        if history:
            if isinstance(history, str):
                user_content = f"Prior task execution history:\n{history}\n\n{user_content}"
            elif isinstance(history, list):
                history_text = "\n".join([
                    f"Role: {m.get('role')}\nContent: {m.get('content')}" 
                    for m in history if isinstance(m, dict)
                ])
                if history_text:
                    user_content = f"Prior task execution history:\n{history_text}\n\n{user_content}"

        messages = [
            {"role": "system", "content": system},
            {"role": "user", "content": user_content},
        ]

        yield {"type": "status", "status": TaskStatus.TESTING}

        params = task.get("params")
        max_rounds = 5
        for _ in range(max_rounds):
            tool_call_in_round = False
            async for chunk in self.stream(messages, tools=TESTER_TOOLS, params=params):
                if chunk["type"] == "token":
                    yield {"type": "token", "text": chunk["text"]}

                elif chunk["type"] == "tool_call":
                    tool_call_in_round = True
                    yield {"type": "tool_call", "call": chunk["call"]}
                    tool_result = await self.dispatch_tool(chunk["call"], conversation_id)

                    # Guard: hard-fail if the sandbox infrastructure is unavailable.
                    # Without this, the model may hallucinate test results from an error string.
                    _infra_failure_markers = (
                        "Docker not found",
                        "WASM fallback failed",
                        "Sandboxed execution is mandatory",
                        "docker: command not found",
                    )
                    if any(m in tool_result for m in _infra_failure_markers):
                        yield {
                            "type": "result",
                            "result": (
                                "TEST INFRASTRUCTURE UNAVAILABLE: Cannot execute tests — the sandbox environment is not running. "
                                "Ensure Docker is started before running agentic test tasks. "
                                f"Raw error: {tool_result}"
                            ),
                        }
                        return

                    messages.append(
                        {
                            "role": "assistant",
                            "content": None,
                            "tool_calls": [chunk["call"]],
                        }
                    )
                    messages.append({"role": "tool", "content": tool_result})

                elif chunk["type"] == "done":
                    if not tool_call_in_round:
                        yield {"type": "result", "result": chunk["full_text"]}
                        return
                    else:
                        messages.append({
                            "role": "assistant",
                            "content": chunk.get("full_text", "")
                        })

        yield {"type": "result", "result": "Max rounds reached."}
