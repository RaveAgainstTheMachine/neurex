"""
core/mcp/servers/neural_harness.py
Universal MCP bridge for the Neurex Neural Harness.
Enables model-agnostic autonomous execution.
"""
from __future__ import annotations
import structlog
from typing import Dict, Any
log = structlog.get_logger()

async def run_neural_harness(query: str, model: str = "qwen2.5-coder:14b") -> str:
    """
    Executes a query using the model-agnostic Neural Harness.
    Defaults to Qwen-2.5-Coder for state-of-the-art open-source performance.
    """
    log.info("neural_harness.invoked", query=query, model=model)
    
    # Create a specialized agent for this model
    from core.context.manager import ContextManager
    from core.agents.base_agent import BaseAgent
    from core.harness.engine import NeuralHarness
    
    agent = BaseAgent(ContextManager())
    agent.agent_type = model
    
    harness = NeuralHarness(agent)
    
    final_result = ""
    async for event in harness.execute(query):
        if event["type"] == "result":
            final_result = event["result"]
            
    return final_result

# Registration logic
TOOL_DEFINITION = {
    "name": "neural_harness",
    "description": "Delegates a complex coding task to the autonomous Neural Harness. Model-agnostic and secure.",
    "input_schema": {
        "type": "object",
        "properties": {
            "query": {"type": "string", "description": "The natural language instruction."},
            "model": {"type": "string", "description": "The model to drive the harness (default: qwen2.5-coder:14b)."}
        },
        "required": ["query"]
    }
}
