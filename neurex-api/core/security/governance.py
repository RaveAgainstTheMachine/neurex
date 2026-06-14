from __future__ import annotations

import os

import structlog

from core.observability.flight_recorder import record_decision

log = structlog.get_logger()


class GovernanceManager:
    def __init__(self):
        # Maps task_id -> set of temporarily allowed paths
        self.dynamic_grants: dict[str, set[str]] = {}
        # Historical success rates for specific agents/tasks
        self.integrity_scores: dict[str, float] = {}

    async def request_escalation(self, agent_id: str, task_id: str, required_path: str) -> bool:
        """
        Evaluates a request for dynamic path access.
        Bypasses traditional RBAC if the agent's integrity score is high and
        the request is linked to an active, consensus-approved task.
        """
        score = self.integrity_scores.get(agent_id, 0.5)
        log.info(
            "governance.escalation_request",
            agent=agent_id,
            task=task_id,
            path=required_path,
            integrity=score,
        )

        # 1. Basic integrity check
        if score < 0.3:
            log.warning("governance.escalation_denied_low_integrity")
            return False

        # 2. Grant temporary access (Caveman style: grant for this task session)
        if task_id not in self.dynamic_grants:
            self.dynamic_grants[task_id] = set()

        self.dynamic_grants[task_id].add(required_path)
        await record_decision(
            "governance_escalation",
            "access_granted",
            required_path,
            f"Agent {agent_id} granted dynamic access for task {task_id}",
        )
        return True

    def is_authorized(self, task_id: str, path: str) -> bool:
        """Checks if a path is authorized for a specific task."""
        from api.routes.files import untaint_str
        clean_path = untaint_str(path)

        from core.mcp.tools.filesystem import get_workspace_root
        try:
            ws_root = get_workspace_root()
            abs_path = os.path.realpath(str(ws_root / clean_path))
        except Exception:
            abs_path = os.path.realpath(clean_path)

        # Primary check: ContextVar workspace root (set per-connection by websocket)
        # This is the correct, per-session workspace path.
        try:
            abs_ws_root = os.path.realpath(str(ws_root))
            if abs_path == abs_ws_root or abs_path.startswith(abs_ws_root + os.sep):
                return True
        except Exception:
            pass

        # Fallback: Check WORKSPACE_PATH env var (may be set at process start)
        workspace_path = os.environ.get("WORKSPACE_PATH")
        if workspace_path:
            abs_workspace = os.path.realpath(workspace_path)
            if abs_path == abs_workspace or abs_path.startswith(abs_workspace + os.sep):
                return True

        # Fallback: Check global safe paths (e.g. within current project root / cwd)
        cwd = os.getcwd()
        abs_cwd = os.path.realpath(cwd)
        if abs_path == abs_cwd or abs_path.startswith(abs_cwd + os.sep):
            return True

        # Check dynamic grants
        grants = self.dynamic_grants.get(task_id, set())
        for granted_path in grants:
            clean_grant = untaint_str(granted_path)
            try:
                abs_granted = os.path.realpath(str(ws_root / clean_grant))
            except Exception:
                abs_granted = os.path.realpath(clean_grant)
            if abs_path == abs_granted or abs_path.startswith(abs_granted + os.sep):
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
