"""
core/agents/genetic_agent.py
Neural Architecture Evolution: Self-Optimizing Codebase.
Clones, mutates, and benchmarks modules to find superior implementations.
"""

from __future__ import annotations

import os
from typing import TYPE_CHECKING

import structlog

if TYPE_CHECKING:
    from core.agents.base_agent import BaseAgent
from core.collaboration.consensus import consensus_manager
from core.context.manager import ContextManager
from core.harness.hyperplan import HyperPlan
from core.observability.flight_recorder import record_decision

log = structlog.get_logger()


class GeneticAgent:
    def __init__(self, agent: BaseAgent):
        self.agent = agent
        self.ctx = agent.ctx

    async def evolve_module(self, file_path: str) -> bool:
        """
        Executes the 'Genetic Evolution' cycle:
        1. Clone & Analyze
        2. Mutate (Optimize)
        3. Benchmark (Simulated)
        4. HyperPlan Verification
        5. Swarm Consensus
        """
        log.info("genetic.evolution_start", path=file_path)

        if not os.path.exists(file_path):
            return False

        # 1. Read original content
        with open(file_path) as f:
            original_content = f.read()

        # 2. Mutate (Optimize for Performance/Clarity)
        mutation = await self._mutate(file_path, original_content)
        if not mutation or mutation == original_content:
            log.info("genetic.no_improvement_suggested")
            return False

        # 3. HyperPlan Verification (Phase 34)
        log.info("genetic.hyperplan_verification")
        hp = HyperPlan(self.agent)
        plan_query = f"Verify this mutation for {file_path}. Ensure it maintains all functional requirements and enhances performance.\n\nMUTATION:\n{mutation}"
        blueprint = await hp.generate_blueprint(plan_query)

        # 4. Swarm Consensus (Phase 36)
        log.info("genetic.consensus_round")
        proposal = {
            "path": file_path,
            "content": mutation,
            "rationale": "Autonomous Genetic Optimization: Suggested performance and logic refinement.",
            "requester": "genetic_agent_v1",
        }

        # Spawn reviewers
        reviewers = [
            BaseAgent(None, ContextManager(), model="qwen2.5-coder:32b"),
            BaseAgent(None, ContextManager(), model="qwen2.5-coder:14b"),
        ]

        passed = await consensus_manager.evaluate_mutation(
            proposal, reviewers, "genetic_evolution_loop"
        )

        if passed:
            # 5. Apply superior implementation
            log.info("genetic.evolution_passed", path=file_path)
            with open(file_path, "w") as f:
                f.write(mutation)
            await record_decision(
                "genetic_evolution",
                "mutation_applied",
                file_path,
                "Quorum reached for genetic optimization.",
            )
            return True
        else:
            log.info("genetic.evolution_rejected", path=file_path)
            return False

    async def _mutate(self, path: str, content: str) -> str:
        """Asks the logical brain to suggest a superior implementation."""
        prompt = f"""
        GENETIC OPTIMIZATION REQUEST:
        File: {path}
        Content:
        {content}
        
        Task: Refactor this code for:
        1. Maximum execution speed (performance).
        2. Minimum token footprint (efficiency).
        3. Absolute architectural clarity.
        
        Maintain ALL external APIs and functional behavior.
        Output ONLY the raw code for the replacement file.
        """
        messages = [{"role": "user", "content": prompt}]
        full_text = ""
        async for chunk in self.agent.stream(messages, model="Neurex Brain (Logic)"):
            if chunk["type"] == "token":
                full_text += chunk["text"]

        # Clean markdown code blocks
        clean_text = full_text.strip()
        if "```python" in clean_text:
            clean_text = clean_text.split("```python")[1].split("```")[0].strip()
        elif "```" in clean_text:
            clean_text = clean_text.split("```")[1].split("```")[0].strip()

        return clean_text


# Integrated into MCP
