"""
core/infrastructure/governance.py
Phase 51: Neural Self-Synthesis (Neural Governance v2.0)
Enables decentralized autonomous decision making (DAO) for Mesh-wide architectural shifts.
Allows nodes to vote on global configuration changes based on reputation and success.
"""

import asyncio
from datetime import datetime

import structlog

log = structlog.get_logger()


class GovernanceProposal:
    def __init__(self, id: str, title: str, description: str, creator_node: str):
        self.id = id
        self.title = title
        self.description = description
        self.creator_node = creator_node
        self.votes: dict[str, bool] = {}  # node_id -> support
        self.created_at = datetime.now()
        self.status = "voting"


class GovernanceDAO:
    def __init__(self):
        self.proposals: dict[str, GovernanceProposal] = {}
        self.dao_lock = asyncio.Lock()

    async def submit_proposal(self, title: str, description: str, creator_node: str) -> str:
        """Submits a new governance proposal to the Mesh DAO with fitness validation."""

        # Phase 51: High-Fitness Governance Requirement
        # We assume the creator_node provides its current fitness for validation
        node_fitness = 25.0  # Placeholder: In prod, this is verified via signed telemetry

        if node_fitness < 20.0:
            log.warning("governance.insufficient_fitness", node=creator_node, fitness=node_fitness)
            raise ValueError("Node fitness insufficient for governance proposal.")

        async with self.dao_lock:
            p_id = f"prop-{hash(title) % 10000}-{datetime.now().strftime('%M%S')}"
            proposal = GovernanceProposal(p_id, title, description, creator_node)
            self.proposals[p_id] = proposal

            log.info("governance.proposal_submitted", id=p_id, title=title)
            return p_id

    async def cast_vote(self, proposal_id: str, node_id: str, support: bool):
        """Casts a vote from a Mesh node on an active proposal."""
        async with self.dao_lock:
            if proposal_id not in self.proposals:
                log.error("governance.proposal_not_found", id=proposal_id)
                return

            proposal = self.proposals[proposal_id]
            if proposal.status != "voting":
                log.warning("governance.voting_closed", id=proposal_id)
                return

            proposal.votes[node_id] = support
            log.info("governance.vote_cast", id=proposal_id, node=node_id, support=support)

            # Phase 51: Autonomous Tallying
            await self._check_consensus(proposal_id)

    async def _check_consensus(self, proposal_id: str):
        """Checks if a proposal has reached the consensus threshold."""
        proposal = self.proposals[proposal_id]
        total_votes = len(proposal.votes)

        # Simple majority consensus for Phase 51
        if total_votes >= 3:  # Min quorum
            support_count = sum(1 for v in proposal.votes.values() if v)
            if support_count / total_votes > 0.66:  # 2/3 Majority
                proposal.status = "passed"
                log.info("governance.proposal_passed", id=proposal_id)
                # Phase 51: Autonomous Execution
                await self._execute_proposal(proposal)

    async def _execute_proposal(self, proposal: GovernanceProposal):
        """Autonomously executes a passed governance proposal."""
        log.info("governance.executing_proposal", id=proposal.id)
        # Simulated execution logic
        await asyncio.sleep(1.0)
        proposal.status = "executed"
        log.info("governance.execution_complete", id=proposal.id)


governance_dao = GovernanceDAO()
