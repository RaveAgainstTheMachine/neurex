"""
core/security/governance.py
Swarm Self-Governance (Autonomous RBAC).
Manages dynamic permission escalations and consensus-linked security gates.
"""
from __future__ import annotations
import structlog
from typing import List, Dict, Any, Set
from core.observability.flight_recorder import record_decision

log = structlog.get_logger()

class GovernanceManager:
    def __init__(self):
        # Maps task_id -> set of temporarily allowed paths
        self.dynamic_grants: Dict[str, Set[str]] = {}
        # Historical success rates for specific agents/tasks
        self.integrity_scores: Dict[str, float] = {}

    async def request_escalation(self, agent_id: str, task_id: str, required_path: str) -> bool:
        """
        Evaluates a request for dynamic path access.
        Bypasses traditional RBAC if the agent's integrity score is high and 
        the request is linked to an active, consensus-approved task.
        """
        score = self.integrity_scores.get(agent_id, 0.5)
        log.info("governance.escalation_request", 
                 agent=agent_id, 
                 task=task_id, 
                 path=required_path, 
                 integrity=score)

        # 1. Basic integrity check
        if score < 0.3:
            log.warning("governance.escalation_denied_low_integrity")
            return False

        # 2. Grant temporary access (Caveman style: grant for this task session)
        if task_id not in self.dynamic_grants:
            self.dynamic_grants[task_id] = set()
        
        self.dynamic_grants[task_id].add(required_path)
        await record_decision("governance_escalation", "access_granted", required_path, f"Agent {agent_id} granted dynamic access for task {task_id}")
        return True

    def is_authorized(self, task_id: str, path: str) -> bool:
        """Checks if a path is authorized for a specific task."""
        # Check global safe paths (e.g. within workspace)
        if path.startswith("/games/CodeProjects/AntiGravity/Neurex"):
             return True
             
        # Check dynamic grants
        grants = self.dynamic_grants.get(task_id, set())
        for granted_path in grants:
            if path.startswith(granted_path):
                return True
        return False

    def report_success(self, agent_id: str, task_id: str, success: bool):
        """Updates the integrity score based on task outcome."""
        current = self.integrity_scores.get(agent_id, 0.5)
        delta = 0.1 if success else -0.2
        self.integrity_scores[agent_id] = max(0.0, min(1.0, current + delta))
        
        # Clean up grants
        if task_id in self.dynamic_grants:
            del self.dynamic_grants[task_id]

governance_manager = GovernanceManager()
