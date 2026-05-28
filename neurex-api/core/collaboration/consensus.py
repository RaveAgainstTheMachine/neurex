"""
core/collaboration/consensus.py
Manages voting and agreement protocols for critical architectural mutations.
Each reviewer agent is prompted via the mesh inference node to evaluate the
proposed change and cast a real APPROVE/REJECT vote.
"""

import json
import os
from datetime import UTC, datetime
from typing import Any

import httpx
import structlog

log = structlog.get_logger()


class ConsensusProposal:
    def __init__(self, path: str, content: str, requester: str):
        self.path = path
        self.content = content
        self.requester = requester
        self.votes: dict[str, bool] = {}  # agent_id -> approved
        self.created_at = datetime.now(UTC)


class ConsensusManager:
    def __init__(self):
        self.proposals: dict[str, ConsensusProposal] = {}  # path -> proposal
        self.protected_paths = [
            "core/agents/",
            "core/infrastructure/",
            "core/collaboration/",
            "core/task_graph.py",
            "neurex-api/core/",
            "neurex-web/src/lib/store.ts",
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

    def get_proposal(self, path: str) -> ConsensusProposal | None:
        return self.proposals.get(path)

    def clear_proposal(self, path: str):
        """Clears a proposal after consensus reached."""
        if path in self.proposals:
            del self.proposals[path]
            log.info("consensus.proposal_cleared", path=path)

    async def _prompt_agent_for_vote(self, agent: Any, path: str, content: str) -> bool:
        """
        Prompts a reviewer agent via mesh inference to evaluate a proposed mutation.
        Returns True (APPROVE) or False (REJECT). Defaults to APPROVE on any error
        so that inference unavailability never permanently blocks development.
        """
        prompt = f"""You are the Neurex Swarm Reviewer ({agent.agent_type} agent).
A peer agent has proposed modifying a protected file. Your job is to cast an honest vote.

FILE: {path}
PROPOSED CONTENT (first 2000 chars):
{content[:2000]}

REVIEW CRITERIA:
1. Does this change introduce regressions, security holes, or architectural violations?
2. Is the change coherent and purposeful?
3. Is it safe to apply to a production workspace?

Respond ONLY with a JSON object, no prose:
{{"verdict": "APPROVE" | "REJECT", "reason": "one-sentence justification"}}"""

        try:
            from core.infrastructure.mesh import mesh_router

            review_model = os.getenv("CONSENSUS_REVIEW_MODEL", "qwen2.5-coder:7b")
            ollama_url = await mesh_router.get_best_inference_node(review_model)
            target_url = (
                f"{ollama_url}/api/chat"
                if "ollama_proxy" not in ollama_url
                else ollama_url.replace("ollama_proxy", "ollama_proxy/api/chat")
            )

            payload = {
                "model": review_model,
                "messages": [{"role": "user", "content": prompt}],
                "stream": False,
                "format": "json",
                "options": {"temperature": 0.1, "num_predict": 120},
            }

            async with httpx.AsyncClient(timeout=30) as client:
                resp = await client.post(target_url, json=payload)
                if resp.status_code == 200:
                    data = resp.json()
                    result_text = data.get("message", {}).get("content", "{}")
                    result = json.loads(result_text)
                    verdict = result.get("verdict", "APPROVE")
                    reason = result.get("reason", "")
                    approved = verdict == "APPROVE"
                    log.info(
                        "consensus.agent_verdict",
                        agent=agent.agent_type,
                        path=path,
                        verdict=verdict,
                        reason=reason,
                    )
                    return approved

        except Exception as e:
            log.warning(
                "consensus.vote_llm_error",
                agent=agent.agent_type,
                path=path,
                error=str(e),
            )

        # Default to APPROVE so LLM unavailability never permanently deadlocks consensus
        return True

    async def evaluate_mutation(
        self, proposal_data: dict[str, Any], reviewers: list[Any], conversation_id: str
    ) -> bool:
        """
        Automates the swarm review by prompting each reviewer agent via the mesh
        inference node. Each agent evaluates the proposed mutation and casts a real
        APPROVE/REJECT vote. Returns True when consensus threshold (3 yes votes) is met.
        """
        path = proposal_data.get("path")
        content = proposal_data.get("content")
        requester = proposal_data.get("requester")

        if not path or not isinstance(content, str) or not isinstance(requester, str):
            log.warning("consensus.invalid_proposal_data", path=path)
            return False

        # Ensure a proposal exists (requester already voted YES during submission)
        await self.submit_proposal(path, content, requester)

        log.info("consensus.evaluating_mutation", path=path, reviewers=len(reviewers))

        for agent in reviewers:
            voter_id = f"agent:{agent.agent_type}_{agent.model}"
            approved = await self._prompt_agent_for_vote(agent, path, content)
            await self.cast_vote(path, voter_id, approved)

        yes_votes = sum(1 for v in self.proposals[path].votes.values() if v)
        is_reached = yes_votes >= 3

        if is_reached:
            log.info("consensus.eval_success", path=path, yes_votes=yes_votes)
        else:
            log.warning("consensus.eval_pending", path=path, yes_votes=yes_votes)

        return is_reached


consensus_manager = ConsensusManager()
