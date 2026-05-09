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
        from core.mcp.client import MCPClient
        self.agent = agent
        self.mcp = MCPClient()
        self.max_steps = 15
        self.history: list[dict[str, str]] = []

    async def execute(self, objective: str) -> AsyncGenerator[dict, None]:
        """Runs the autonomous loop to achieve the objective."""
        log.info("harness.session_start", objective=objective, model=self.agent.agent_type)
        
        self.history = [
            {"role": "system", "content": self._get_system_prompt()},
            {"role": "user", "content": f"Objective: {objective}"}
        ]
        
        for step in range(self.max_steps):
            log.info("harness.step_start", step=step)
            yield {"type": "status", "status": f"thinking_step_{step}"}
            
            # 1. Thought & Action Generation
            full_response = ""
            async for chunk in self.agent.stream(self.history):
                if chunk["type"] == "token":
                    full_response += chunk["text"]
                elif chunk["type"] == "done":
                    break
            
            self.history.append({"role": "assistant", "content": full_response})
            
            # 2. Parse Tool Calls (Simulated for this implementation)
            # In a real setup, we use a regex or JSON parser to extract tool calls from the response.
            tool_calls = self._parse_tool_calls(full_response)
            
            if not tool_calls:
                yield {"type": "result", "result": full_response}
                break
                
            # 3. Execution
            for call in tool_calls:
                yield {"type": "status", "status": f"executing_{call['tool']}"}
                observation = await self.mcp.call(call["tool"], call["args"])
                self.history.append({"role": "user", "content": f"Observation from {call['tool']}:\n{observation}"})
                
        log.info("harness.session_complete")

    def _get_system_prompt(self) -> str:
        return """
        You are the Neurex Neural Harness. Your goal is to achieve the objective autonomously.
        Use the following tools to interact with the environment:
        - read_file(path)
        - write_file(path, content)
        - run_command(command)
        - grep_search(query)
        
        Always wrap your tool calls in XML tags:
        <tool_call name="tool_name">
        {"arg1": "value"}
        </tool_call>
        
        Think step-by-step. Plan your actions. Review observations.
        """

    def _parse_tool_calls(self, text: str) -> list[dict[str, Any]]:
        import json
        import re
        pattern = r'<tool_call name="(\w+)">\s*(.*?)\s*</tool_call>'
        matches = re.findall(pattern, text, re.DOTALL)
        calls = []
        for name, args_raw in matches:
            try:
                calls.append({"tool": name, "args": json.loads(args_raw)})
            except (json.JSONDecodeError, ValueError):
                continue
        return calls
