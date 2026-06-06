"""
core/agents/researcher_agent.py
Researcher agent. Uses web search to find documentation, libraries, and solutions.
"""

from __future__ import annotations

from collections.abc import AsyncGenerator

import structlog

from core.agents.base_agent import BaseAgent
from core.task_graph import TaskStatus

log = structlog.get_logger()

RESEARCHER_TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "web_search",
            "description": "Search the web for technical documentation, library usage, or bug fixes.",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {"type": "string", "description": "The search query"},
                    "max_results": {
                        "type": "integer",
                        "description": "Number of results to return, default 5",
                    },
                },
                "required": ["query"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "run_command",
            "description": "Run a shell command inside the workspace container. Use for: grep, find, cat. Output is captured and returned.",
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

RESEARCHER_SYSTEM = """\
You are a senior technical researcher inside Neurex IDE.
Your goal is to find accurate, up-to-date documentation and code examples to assist the Coder and Architect.
You have access to web search AND local workspace shell tools. 
When searching:
1. Be specific with your queries (e.g., 'FastAPI ChromaDB integration example').
2. If researching the local codebase, use `run_command` with `grep` or `find` to locate files and lines BEFORE using LSP tools. DO NOT guess file paths or line numbers for LSP tools! DO NOT assume the project language (e.g., Java).
3. Summarize the findings clearly.
4. Provide links to original sources.
"""


class ResearcherAgent(BaseAgent):
    """Agent specialized in external research and documentation retrieval."""

    system_prompt: str = RESEARCHER_SYSTEM
    agent_type: str = "researcher"

    async def execute(self, task: dict, conversation_id: str) -> AsyncGenerator[dict, None]:
        description = task.get("description", "")

        # Rule 76: Call rag_context at start of execute
        rag = await self.rag_context(description, n=3)
        # Rule 77: Pass RAG to build_system_prompt
        system = await self.build_system_prompt(conversation_id, rag)

        history = task.get("history", "")
        user_content = f"Find information related to: {description}"
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
        log.info("agent.researcher.start", task=task.get("title"), conversation_id=conversation_id)

        params = task.get("params")
        # Rule 71: max_rounds guard
        max_rounds = 5
        for _ in range(max_rounds):
            tool_call_in_round = False
            async for chunk in self.stream(messages, tools=RESEARCHER_TOOLS, params=params):
                if chunk["type"] == "token":
                    yield {"type": "token", "text": chunk["text"]}

                elif chunk["type"] == "tool_call":
                    tool_call_in_round = True
                    yield {"type": "tool_call", "call": chunk["call"]}

                    tool_result = await self.dispatch_tool(chunk["call"], conversation_id)

                    # Rule 72: Append both assistant and tool messages
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

                elif chunk["type"] == "done":
                    # If no tool calls in this round, we're done
                    if not tool_call_in_round:
                        log.info("agent.researcher.done", task=task.get("title"))
                        yield {"type": "result", "result": chunk["full_text"]}
                        return
                    else:
                        messages.append({
                            "role": "assistant",
                            "content": chunk.get("full_text", "")
                        })

        log.warning("agent.researcher.max_rounds", task=task.get("title"))
        yield {"type": "result", "result": "Researcher reached maximum tool rounds."}
