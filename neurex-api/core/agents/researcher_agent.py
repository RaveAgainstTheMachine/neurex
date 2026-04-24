"""
core/agents/researcher_agent.py
Researcher agent. Uses web search to find documentation, libraries, and solutions.
"""
from __future__ import annotations
from typing import AsyncGenerator
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
                    "max_results": {"type": "integer", "description": "Number of results to return, default 5"}
                },
                "required": ["query"],
            },
        },
    },
]

RESEARCHER_SYSTEM = """\
You are a senior technical researcher inside Neurex IDE.
Your goal is to find accurate, up-to-date documentation and code examples to assist the Coder and Architect.
You have access to web search tools. 
When searching:
1. Be specific with your queries (e.g., 'FastAPI ChromaDB integration example').
2. Summarize the findings clearly.
3. Provide links to original sources.
"""

class ResearcherAgent(BaseAgent):
    """Agent specialized in external research and documentation retrieval."""
    
    system_prompt: str = RESEARCHER_SYSTEM
    agent_type: str = "researcher"

    async def execute(
        self, task: dict, conversation_id: str
    ) -> AsyncGenerator[dict, None]:
        description = task.get("description", "")
        
        # Rule 76: Call rag_context at start of execute
        rag = await self.rag_context(description, n=3)
        # Rule 77: Pass RAG to build_system_prompt
        system = self.build_system_prompt(rag)

        messages = [
            {"role": "system",  "content": system},
            {"role": "user",    "content": f"Find information related to: {description}"},
        ]

        yield {"type": "status", "status": TaskStatus.THINKING}
        log.info("agent.researcher.start", task=task.get("title"), conversation_id=conversation_id)

        # Rule 71: max_rounds guard
        max_rounds = 5
        for _ in range(max_rounds):
            async for chunk in self.stream(messages, tools=RESEARCHER_TOOLS):
                if chunk["type"] == "token":
                    yield {"type": "token", "text": chunk["text"]}

                elif chunk["type"] == "tool_call":
                    yield {"type": "tool_call", "call": chunk["call"]}
                    
                    tool_result = await self.dispatch_tool(chunk["call"])

                    # Rule 72: Append both assistant and tool messages
                    messages.append({
                        "role": "assistant",
                        "content": None,
                        "tool_calls": [chunk["call"]],
                    })
                    messages.append({
                        "role": "tool",
                        "content": tool_result,
                    })

                elif chunk["type"] == "done":
                    # If no tool calls in last round, we're done
                    if not any(m.get("role") == "tool" for m in messages[-2:]):
                        log.info("agent.researcher.done", task=task.get("title"))
                        yield {"type": "result", "result": chunk["full_text"]}
                        return

        log.warning("agent.researcher.max_rounds", task=task.get("title"))
        yield {"type": "result", "result": "Researcher reached maximum tool rounds."}
