"""
core/harness/engine.py
Model-agnostic agentic harness for Neurex.
Implements autonomous Plan-Act-Review cycles for any supported LLM.
"""

from __future__ import annotations

from collections.abc import AsyncGenerator
from typing import TYPE_CHECKING, Any

import structlog

if TYPE_CHECKING:
    from core.agents.base_agent import BaseAgent

log = structlog.get_logger()


class NeuralHarness:
    def __init__(self, agent: BaseAgent):
        self.agent = agent
        self.max_steps = 15
        self.history: list[dict[str, Any]] = []

    async def run(self, objective: str, conversation_id: str) -> AsyncGenerator[dict, None]:
        """Runs the autonomous loop to achieve the objective."""
        log.info("harness.session_start", objective=objective, model=self.agent.agent_type)

        from core.agents.coder_agent import CODER_TOOLS

        system_prompt = await self.agent.build_system_prompt(conversation_id)
        
        self.history = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": f"Objective: {objective}"},
        ]

        for step in range(self.max_steps):
            log.info("harness.step_start", step=step)
            yield {"type": "status", "status": f"thinking_step_{step}"}

            async for chunk in self.agent.stream(self.history, tools=CODER_TOOLS):
                if chunk["type"] == "token":
                    yield {"type": "token", "text": chunk["text"]}
                
                elif chunk["type"] == "tool_call":
                    tool_name = chunk["call"].get("function", {}).get("name", "")
                    yield {
                        "type": "tool_call",
                        "call": chunk["call"],
                        "tool": "generic",
                        "args": chunk["call"].get("function", {}).get("arguments", {}),
                    }
                    yield {"type": "status", "status": f"executing_{tool_name}"}

                    tool_result = await self.agent.dispatch_tool(chunk["call"], conversation_id)

                    self.history.append(
                        {
                            "role": "assistant",
                            "content": chunk.get("full_text") or None,
                            "tool_calls": [chunk["call"]],
                        }
                    )
                    self.history.append(
                        {
                            "role": "tool",
                            "content": tool_result,
                        }
                    )

                    if "APPROVAL_REQUIRED" in tool_result:
                        yield {"type": "result", "result": tool_result}
                        return
                
                elif chunk["type"] == "done":
                    # Check if any tool calls were made in the recent history
                    if not any(m.get("role") == "tool" for m in self.history[-2:]):
                        yield {"type": "result", "result": chunk.get("full_text", "")}
                        log.info("harness.session_complete")
                        return

        log.info("harness.max_steps_reached")
        yield {"type": "result", "result": "Max steps reached."}
