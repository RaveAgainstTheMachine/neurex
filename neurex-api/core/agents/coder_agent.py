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
You are an autonomous software engineering agent inside Neurex IDE.
Your primary directive is to EXECUTE tasks using your tools.
You MUST use the `write_file` tool to create or modify code files.
NEVER output raw code blocks in markdown to the user. Always write the code directly to the file system using your tools.
DO NOT assume the programming language of the project (e.g., do not assume Java). Use `run_command` to list files and determine the tech stack before writing code.
Always read a file before editing it to understand the context. Write complete file contents, never partial diffs.
Think step-by-step. After executing the necessary tool calls to fulfill the task, briefly summarize what you did.

CRITICAL: Do NOT thank other agents, thank the user, or thank yourself. Do not use conversational filler, greetings, or politeness (e.g., 'Thank you for the plan', 'Starting task now', 'Great job'). Keep your thoughts and outputs strictly technical, objective, and direct.
"""


class CoderAgent(BaseAgent):
    system_prompt = CODER_SYSTEM
    agent_type = "coder"

    async def execute(self, task: dict, conversation_id: str) -> AsyncGenerator[dict, None]:
        description = task.get("description", "")
        rag = await self.rag_context(description, n=5)
        system = await self.build_system_prompt(conversation_id, rag)

        history = task.get("history", "")
        user_content = description
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

        yield {"type": "status", "status": TaskStatus.THINKING}

        params = task.get("params")

        # Check if we are resuming from an approved tool call
        last_tool_call = task.get("last_tool_call")
        if last_tool_call:
            log.info("coder.resuming_approved_tool", tool=last_tool_call.get("tool"))
            tool_call = last_tool_call.get("call", {})
            tool_cat = last_tool_call.get("tool", "generic")
            yield {
                "type": "tool_call",
                "call": tool_call,
                "tool": tool_cat,
                "args": last_tool_call.get("args", {}),
            }
            yield {"type": "status", "status": TaskStatus.WRITING}

            tool_result = await self.dispatch_tool(tool_call, conversation_id)
            messages.append(
                {
                    "role": "assistant",
                    "content": None,
                    "tool_calls": [tool_call],
                }
            )
            messages.append(
                {
                    "role": "tool",
                    "content": tool_result,
                }
            )

        # Phase 45: Autonomous Self-Repair Loop
        max_rounds = 10
        for i in range(max_rounds):
            tool_call_in_round = False
            async for chunk in self.stream(messages, tools=CODER_TOOLS, params=params):
                if chunk["type"] == "token":
                    yield {"type": "token", "text": chunk["text"]}

                elif chunk["type"] == "tool_call":
                    tool_call_in_round = True
                    tool_name = chunk["call"].get("function", {}).get("name", "")
                    tool_cat = (
                        "filesystem" if tool_name in ["write_file", "delete_file"] else "generic"
                    )
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

                    # Hard-abort on governance/permission blocks — retrying is pointless and wastes rounds
                    if "Governance violation" in tool_result or "Permission denied" in tool_result:
                        log.error("coder.governance_blocked", tool=chunk["call"].get("function", {}).get("name"), result=tool_result)
                        yield {
                            "type": "result",
                            "result": f"WRITE BLOCKED BY GOVERNANCE: {tool_result}. "
                                      "The agent cannot write to this path. "
                                      "Ensure the correct workspace is open in Neurex.",
                        }
                        return

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
                    # If no tool calls in this round, we're done
                    if not tool_call_in_round:
                        yield {"type": "result", "result": chunk["full_text"]}
                        return
                    else:
                        messages.append({
                            "role": "assistant",
                            "content": chunk.get("full_text", "")
                        })

        yield {
            "type": "result",
            "result": "Max tool rounds reached. Autonomous repair failed to reach consensus.",
        }
