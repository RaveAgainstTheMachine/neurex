"""
core/harness/hyperplan.py
HYPERPLAN: Deep Thinking & Multi-Pass Architecture Planning.
Offloads complex design tasks to a high-compute reasoning loop.
"""

from __future__ import annotations

import asyncio
from typing import TYPE_CHECKING, Any

import structlog

if TYPE_CHECKING:
    from core.agents.base_agent import BaseAgent

log = structlog.get_logger()


class HyperPlan:
    def __init__(self, agent: BaseAgent):
        self.agent = agent
        self.ctx = agent.ctx

    async def generate_blueprint(self, task_description: str) -> dict[str, Any]:
        """
        Executes the 4-pass HYPERPLAN cycle with predictive prefetching.
        """
        log.info("hyperplan.start", task=task_description[:50])

        # Phase 44.8: Predictive Context Prefetching
        # Start RAG search in background while Pass 1 generates decomposition
        context_task = asyncio.create_task(
            self.ctx.explorer.hybrid_search(task_description, limit=15)
        )

        # Pass 1: Decomposition
        decomp = await self._pass_decomposition(task_description)

        # Ensure context is ready for Pass 2
        retrieved_context = await context_task
        log.info("hyperplan.context_primed", results=len(retrieved_context))

        # Pass 2: Symbolic Trace (Context-aware)
        trace = await self._pass_symbolic_trace(decomp, retrieved_context)

        # Pass 3: Optimization & Security
        optimized = await self._pass_optimization(trace)

        # Pass 4: Final Blueprint Synthesis
        blueprint = await self._pass_synthesis(optimized)

        log.info("hyperplan.complete")
        return blueprint

    async def _pass_decomposition(self, task: str) -> str:
        prompt = f"HYPERPLAN PASS 1: DECOMPOSITION\nBreak this task into high-level modules and data flows.\nTask: {task}"
        return await self._ask_brain(prompt, self.agent.model)

    async def _pass_symbolic_trace(self, decomp: str, context: list[dict[str, Any]]) -> str:
        ctx_text = "\n".join([r.get("document", "") for r in context])
        prompt = f"HYPERPLAN PASS 2: SYMBOLIC TRACE\nAnalyze the data flows and identify potential side effects or race conditions.\nDecomposition: {decomp}\nCode Context:\n{ctx_text}"
        return await self._ask_brain(prompt, self.agent.model)

    async def _pass_optimization(self, trace: str) -> str:
        prompt = f"HYPERPLAN PASS 3: OPTIMIZATION\nOptimize the architecture for performance, security (RBAC), and token efficiency.\nAnalysis: {trace}"
        return await self._ask_brain(prompt, self.agent.model)

    async def _pass_synthesis(self, optimized: str) -> dict[str, Any]:
        prompt = f"""HYPERPLAN PASS 4: SYNTHESIS
Output the final, structured execution blueprint in JSON format.
You must output a "tasks" array containing the sub-tasks:
{{
  "tasks": [
    {{"agent": "coder|tester|researcher|reviewer|swarm", "title": "Short descriptive title", "description": "EXTREMELY DETAILED step-by-step instructions. MUST NOT BE EMPTY OR REPEAT THE TITLE."}}
  ]
}}
Optimization: {optimized}"""
        raw_json = await self._ask_brain(prompt, self.agent.model)
        try:
            import json
            import re
            cleaned = re.sub(r"```(?:json)?", "", raw_json).strip().rstrip("`")
            match = re.search(r"(\{.*\})", cleaned, re.DOTALL)
            if match:
                return json.loads(match.group(1))
            return json.loads(cleaned)
        except (json.JSONDecodeError, ValueError):
            return {"raw_blueprint": raw_json}

    async def _ask_brain(self, prompt: str, model: str) -> str:
        """Helper to stream from the logical brain and collect response."""
        full_text = ""
        system_prompt = getattr(self.agent, "system_prompt", "")
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})
        async for chunk in self.agent.stream(messages, model=model):
            if chunk["type"] == "token":
                full_text += chunk["text"]
        return full_text


# Integrated into MCP
