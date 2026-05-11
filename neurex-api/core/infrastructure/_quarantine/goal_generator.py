"""
core/infrastructure/goal_generator.py
Phase 50: The Sentient Singularity (Autonomous Goal Setting)
Enables the Neurex Mesh to autonomously propose its own engineering goals 
based on codebase entropy, architectural debt, and mission success telemetry.
"""
import asyncio

import structlog

from core.infrastructure.evolution import evolution_coordinator

log = structlog.get_logger()

class EvolutionaryGoal:
    def __init__(self, id: str, title: str, description: str, priority: int, domain: str):
        self.id = id
        self.title = title
        self.description = description
        self.priority = priority # 1-10
        self.domain = domain
        self.status = "proposed"

class GoalGenerator:
    def __init__(self):
        self.proposed_goals: list[EvolutionaryGoal] = []
        self.generator_lock = asyncio.Lock()

    async def analyze_and_propose_goals(self):
        """
        Analyzes the Mesh's state (evolution versions, repair rates, etc.) 
        and proposes strategic engineering goals to the swarm.
        """
        async with self.generator_lock:
            log.info("goal_generator.analyzing_mesh_entropy")
            
            # Phase 50: Sentient Codebase Analysis
            # 1. Identify domains with high version churn but low fitness (Struggling Adapters)
            # 2. Identify areas with high 'MUTATION_REJECTED' telemetry
            # 3. Propose 'Structural Refactoring' missions
            
            goals = []
            for domain, adapter in evolution_coordinator.adapters.items():
                if adapter.version > 5 and adapter.fitness_score < 20.0:
                    goals.append(EvolutionaryGoal(
                        id=f"goal-{domain}-refactor",
                        title=f"Autonomous Structural Refactoring: {domain}",
                        description=f"The adapter for {domain} has high churn (v{adapter.version}) but low fitness. Proposing a structural redesign of the domain's core logic to resolve architectural friction.",
                        priority=8,
                        domain=domain
                    ))

            if goals:
                self.proposed_goals.extend(goals)
                log.info("goal_generator.goals_proposed", count=len(goals))
            
            return goals

    def get_pending_goals(self) -> list[EvolutionaryGoal]:
        """Retrieves all goals that require swarm consensus or user approval."""
        return [g for g in self.proposed_goals if g.status == "proposed"]

goal_generator = GoalGenerator()
