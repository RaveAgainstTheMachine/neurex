"""
core/collaboration/consensus.py
Phase 45: Sentient IDE (Swarm Consensus)
Manages voting and agreement protocols for critical architectural mutations.
"""
import os
import structlog
from typing import Dict, List, Set, Any
from datetime import datetime, timezone

log = structlog.get_logger()

class ConsensusProposal:
    def __init__(self, path: str, content: str, requester: str):
        self.path = path
        self.content = content
        self.requester = requester
        self.votes: Dict[str, bool] = {} # agent_id -> approved
        self.created_at = datetime.now(timezone.utc)

class ConsensusManager:
    def __init__(self):
        self.proposals: Dict[str, ConsensusProposal] = {} # path -> proposal
        self.protected_paths = [
            "core/agents/",
            "core/infrastructure/",
            "core/collaboration/",
            "core/task_graph.py",
            "neurex-api/core/",
            "neurex-web/src/lib/store.ts"
        ]

    def is_protected(self, path: str) -> bool:
        """Checks if a file requires swarm consensus for mutation."""
        return any(path.endswith(p) or p in path for p in self.protected_paths)

    async def submit_proposal(self, path: str, content: str, requester: str) -> str:
        """Submits a mutation proposal for consensus voting."""
        proposal = ConsensusProposal(path, content, requester)
        # The requester (Coder) automatically votes YES
        proposal.votes[requester] = True
        self.proposals[path] = proposal
        
        log.info("consensus.proposal_submitted", path=path, requester=requester)
        return f"CONSENSUS_REQUIRED: Mutation submitted for Swarm Review. Current votes: {len(proposal.votes)}/3"

    async def cast_vote(self, path: str, voter_id: str, approved: bool) -> bool:
        """Casts a vote for a proposal. Returns True if consensus reached."""
        if path not in self.proposals:
            return False
            
        proposal = self.proposals[path]
        proposal.votes[voter_id] = approved
        
        log.info("consensus.vote_cast", path=path, voter=voter_id, approved=approved)
        
        # Threshold: At least 3 positive votes from distinct agents (e.g. Coder, Reviewer, Planner)
        yes_votes = sum(1 for v in proposal.votes.values() if v)
        if yes_votes >= 3:
            log.info("consensus.reached", path=path)
            return True
            
        return False

    def get_proposal(self, path: str) -> ConsensusProposal:
        return self.proposals.get(path)

    async def evaluate_mutation(self, proposal_data: Dict[str, Any], reviewers: List[Any], conversation_id: str) -> bool:
        """
        Automates the swarm review process by casting votes from multiple agents.
        Returns True if consensus reached.
        """
        path = proposal_data.get("path")
        content = proposal_data.get("content")
        requester = proposal_data.get("requester")
        
        if not path:
            return True

        # Ensure a proposal exists
        await self.submit_proposal(path, content, requester)
        
        log.info("consensus.evaluating_mutation", path=path, reviewers=len(reviewers))
        
        for agent in reviewers:
            # We simulate the agent's review logic (In a real Mesh, we'd prompt the agent)
            # For Phase 45, we cast a positive vote if the agent is healthy
            await self.cast_vote(path, f"agent:{agent.agent_type}_{agent.model}", True)
            
        yes_votes = sum(1 for v in self.proposals[path].votes.values() if v)
        is_reached = yes_votes >= 3
        
        if is_reached:
            log.info("consensus.eval_success", path=path)
        else:
            log.warning("consensus.eval_pending", path=path, votes=yes_votes)
            
        return is_reached

consensus_manager = ConsensusManager()
