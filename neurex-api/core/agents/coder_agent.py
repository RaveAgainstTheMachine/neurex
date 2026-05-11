"""
core/agents/coder_agent.py
Writes, edits, and refactors code files using MCP filesystem tools.
"""

from __future__ import annotations

from collections.abc import AsyncGenerator

import structlog

from core.agents.base_agent import BaseAgent
from core.task_graph import TaskStatus

log = structlog.get_logger()

CODER_TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "read_file",
            "description": "Read the contents of a file in the workspace.",
            "parameters": {
                "type": "object",
                "properties": {
                    "path": {"type": "string", "description": "Relative path from workspace root"}
                },
                "required": ["path"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "write_file",
            "description": "Write or overwrite a file in the workspace.",
            "parameters": {
                "type": "object",
                "properties": {
                    "path": {"type": "string"},
                    "content": {"type": "string"},
                },
                "required": ["path", "content"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "list_directory",
            "description": "List the contents of a directory in the workspace.",
            "parameters": {
                "type": "object",
                "properties": {
                    "path": {"type": "string", "description": "Relative path, default '.'"}
                },
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "grep_search",
            "description": "Search for a string across the codebase.",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {"type": "string", "description": "Search term"},
                    "include_globs": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "Optional file globs to include",
                    },
                },
                "required": ["query"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "delete_file",
            "description": "Move a file to the workspace trash.",
            "parameters": {
                "type": "object",
                "properties": {"path": {"type": "string"}},
                "required": ["path"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "run_command",
            "description": "Execute a shell command in the workspace sandbox.",
            "parameters": {
                "type": "object",
                "properties": {
                    "command": {"type": "string", "description": "The shell command to run"},
                    "cwd": {"type": "string", "description": "Working directory, default '.'"},
                },
                "required": ["command"],
            },
        },
    },
]


CODER_SYSTEM = """\
You are an expert software engineer inside Neurex IDE.
You have access to filesystem tools to read and write files in the workspace.
Always read a file before editing it. Write complete file contents, never partial diffs.
Think step-by-step. After writing files, briefly summarize what you did.
"""


class CoderAgent(BaseAgent):
    system_prompt = CODER_SYSTEM
    agent_type = "coder"

    async def execute(self, task: dict, conversation_id: str) -> AsyncGenerator[dict, None]:
        description = task.get("description", "")
        rag = await self.rag_context(description, n=5)
        system = await self.build_system_prompt(conversation_id, rag)

        messages = [
            {"role": "system", "content": system},
            {"role": "user", "content": description},
        ]

        yield {"type": "status", "status": TaskStatus.THINKING}

        params = task.get("params")

        # Phase 45: Autonomous Self-Repair Loop
        max_rounds = 10
        for i in range(max_rounds):
            async for chunk in self.stream(messages, tools=CODER_TOOLS, params=params):
                if chunk["type"] == "token":
                    yield {"type": "token", "text": chunk["text"]}

                elif chunk["type"] == "tool_call":
                    tool_name = chunk["call"].get("function", {}).get("name", "")
                    tool_cat = "filesystem" if tool_name in ["write_file", "delete_file"] else "generic"
                    if tool_name == "run_command":
                        tool_cat = "shell"

                    yield {
                        "type": "tool_call",
                        "call": chunk["call"],
                        "tool": tool_cat,
                        "args": chunk["call"].get("function", {}).get("arguments", {}),
                    }
                    yield {"type": "status", "status": TaskStatus.WRITING}

                    tool_result = await self.dispatch_tool(chunk["call"], conversation_id)

                    # Phase 45: Mutation Reflection & Repair
                    if "MUTATION_REJECTED" in tool_result:
                        yield {"type": "status", "status": "REPAIRING"}
                        log.warning("self_repair_triggered", iteration=i, reason=tool_result)
                        # The tool_result contains the architectural reason; the agent will read it in the next loop

                    # Append tool exchange to history
                    messages.append(
                        {
                            "role": "assistant",
                            "content": None,
                            "tool_calls": [chunk["call"]],
                        }
                    )
                    messages.append(
                        {
                            "role": "tool",
                            "content": tool_result,
                        }
                    )

                    if "APPROVAL_REQUIRED" in tool_result:
                        yield {"type": "result", "result": tool_result}
                        return

                elif chunk["type"] == "done":
                    # If no tool calls in last round, we're done
                    if not any(m.get("role") == "tool" for m in messages[-2:]):
                        # Phase 48: Record Success for Neural Evolution
                        from core.infrastructure.evolution import evolution_coordinator

                        domain = task.get("domain", "generic-coding")
                        await evolution_coordinator.record_success(domain, {"quality_score": 1.0})

                        yield {"type": "result", "result": chunk["full_text"]}
                        return

        yield {
            "type": "result",
            "result": "Max tool rounds reached. Autonomous repair failed to reach consensus.",
        }
