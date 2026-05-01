"""
core/collaboration/consensus.py
Neural Swarm Consensus: Implements voting-based code mutations.
Ensures that multiple agents approve major architectural changes before application.
"""
from __future__ import annotations
import structlog
from typing import List, Dict, Any
from core.observability.flight_recorder import record_decision

log = structlog.get_logger()

class ConsensusManager:
    def __init__(self, threshold: float = 0.66):
        self.threshold = threshold # Quorum percentage

    async def evaluate_mutation(self, proposal: Dict[str, Any], reviewers: List[Any], conversation_id: str) -> bool:
        """
        Coordinates a voting cycle among reviewer agents.
        Proposal: {"path": "...", "content": "...", "rationale": "..."}
        """
        votes = []
        log.info("consensus.start_cycle", path=proposal["path"], reviewer_count=len(reviewers))
        
        for agent in reviewers:
            try:
                vote = await self._collect_vote(agent, proposal)
                votes.append(vote)
                log.info("consensus.vote_received", agent=agent.agent_type, approved=vote["approved"])
            except Exception as e:
                log.warning("consensus.reviewer_failed", agent=agent.agent_type, error=str(e))

        if not votes:
            return False

        approvals = sum(1 for v in votes if v["approved"])
        score = approvals / len(votes)
        is_passed = score >= self.threshold

        # Record the outcome
        summary = {
            "path": proposal["path"],
            "score": score,
            "passed": is_passed,
            "votes": votes
        }
        await record_decision(conversation_id, "consensus_engine", "mutation_vote", str(summary))
        
        log.info("consensus.cycle_complete", passed=is_passed, score=score)
        return is_passed

    async def _collect_vote(self, agent, proposal: Dict[str, Any]) -> Dict[str, Any]:
        """Asks an agent to review a mutation proposal."""
        prompt = f"""
        CONSENSUS REVIEW REQUEST:
        File: {proposal['path']}
        Rationale: {proposal['rationale']}
        Proposed Content Snippet:
        {proposal['content'][:1000]}
        
        Analyze this change for:
        1. Architectural integrity.
        2. Performance regressions.
        3. Security vulnerabilities.
        
        Output your vote in JSON: {{"approved": true/false, "rationale": "..."}}
        """
        messages = [{"role": "user", "content": prompt}]
        full_text = ""
        async for chunk in agent.stream(messages):
            if chunk["type"] == "token":
                full_text += chunk["text"]
        
        try:
            import json
            # Extract JSON from potential markdown
            clean_text = full_text.strip()
            if "```json" in clean_text:
                clean_text = clean_text.split("```json")[1].split("```")[0].strip()
            return json.loads(clean_text)
        except:
            return {"approved": False, "rationale": f"Failed to parse vote: {full_text[:100]}"}

consensus_manager = ConsensusManager()
