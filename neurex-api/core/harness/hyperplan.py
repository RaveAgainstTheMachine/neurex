"""
core/harness/hyperplan.py
HYPERPLAN: Deep Thinking & Multi-Pass Architecture Planning.
Offloads complex design tasks to a high-compute reasoning loop.
"""
from __future__ import annotations
import asyncio
import structlog
from typing import List, Dict, Any
from core.agents.base_agent import BaseAgent
from core.context.manager import ContextManager

log = structlog.get_logger()

class HyperPlan:
    def __init__(self, agent: BaseAgent):
        self.agent = agent
        self.ctx = agent.ctx

    async def generate_blueprint(self, task_description: str) -> Dict[str, Any]:
        """
        Executes the 4-pass HYPERPLAN cycle:
        1. Decomposition
        2. Symbolic Trace
        3. Optimization
        4. Final Blueprint
        """
        log.info("hyperplan.start", task=task_description[:50])
        
        # Pass 1: Decomposition
        decomp = await self._pass_decomposition(task_description)
        
        # Pass 2: Symbolic Trace (Context-aware)
        trace = await self._pass_symbolic_trace(decomp)
        
        # Pass 3: Optimization & Security
        optimized = await self._pass_optimization(trace)
        
        # Pass 4: Final Blueprint Synthesis
        blueprint = await self._pass_synthesis(optimized)
        
        log.info("hyperplan.complete")
        return blueprint

    async def _pass_decomposition(self, task: str) -> str:
        prompt = f"HYPERPLAN PASS 1: DECOMPOSITION\nBreak this task into high-level modules and data flows.\nTask: {task}"
        return await self._ask_brain(prompt, "Neurex Brain (Logic)")

    async def _pass_symbolic_trace(self, decomp: str) -> str:
        prompt = f"HYPERPLAN PASS 2: SYMBOLIC TRACE\nAnalyze the data flows and identify potential side effects or race conditions.\nContext: {decomp}"
        return await self._ask_brain(prompt, "Neurex Brain (Logic)")

    async def _pass_optimization(self, trace: str) -> str:
        prompt = f"HYPERPLAN PASS 3: OPTIMIZATION\nOptimize the architecture for performance, security (RBAC), and token efficiency.\nAnalysis: {trace}"
        return await self._ask_brain(prompt, "Neurex Brain (Logic)")

    async def _pass_synthesis(self, optimized: str) -> Dict[str, Any]:
        prompt = f"HYPERPLAN PASS 4: SYNTHESIS\nOutput the final, structured execution blueprint in JSON format.\nOptimization: {optimized}"
        raw_json = await self._ask_brain(prompt, "Neurex Brain (Logic)")
        try:
            import json
            return json.loads(raw_json)
        except:
            return {"raw_blueprint": raw_json}

    async def _ask_brain(self, prompt: str, model: str) -> str:
        """Helper to stream from the logical brain and collect response."""
        full_text = ""
        messages = [{"role": "user", "content": prompt}]
        async for chunk in self.agent.stream(messages, model=model):
            if chunk["type"] == "token":
                full_text += chunk["text"]
        return full_text

# Integrated into MCP
