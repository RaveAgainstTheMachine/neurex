from __future__ import annotations

import asyncio
import json
import os
from pathlib import Path

import structlog

from core.observability.flight_recorder import record_decision

log = structlog.get_logger()

# Path for durable grants storage
def get_grants_file() -> Path:
    from core.mcp.tools.filesystem import get_workspace_root
    try:
        return get_workspace_root() / ".neurex" / "grants.json"
    except Exception:
        return Path(os.getenv("WORKSPACE_PATH", "/workspace")) / ".neurex" / "grants.json"


class GovernanceManager:
    def __init__(self):
        # Maps task_id -> set of temporarily allowed paths
        self.dynamic_grants: dict[str, set[str]] = {}
        self.pending_approvals: dict[str, asyncio.Future[bool]] = {}
        self._load_grants()

    def _load_grants(self):
        grants_file = get_grants_file()
        if grants_file.exists():
            try:
                with open(grants_file) as f:
                    data = json.load(f)
                    self.dynamic_grants = {k: set(v) for k, v in data.items()}
            except Exception as e:
                log.error("governance.load_grants_failed", error=str(e))

    def _save_grants(self):
        grants_file = get_grants_file()
        try:
            grants_file.parent.mkdir(parents=True, exist_ok=True)
            with open(grants_file, "w") as f:
                data = {k: list(v) for k, v in self.dynamic_grants.items()}
                json.dump(data, f)
        except Exception as e:
            log.error("governance.save_grants_failed", error=str(e))

    async def request_escalation(self, session_id: str, path: str, reason: str) -> bool:
        """
        Dispatches a path escalation proposal via WebSocket and suspends
        execution until the user confirms (Approve) or declines (Deny).
        """
        log.info(
            "governance.escalation_request",
            session=session_id,
            path=path,
            reason=reason,
        )

        loop = asyncio.get_running_loop()
        fut = loop.create_future()
        # Create a unique approval ID for this specific request
        import uuid
        approval_id = f"escalation_{uuid.uuid4().hex[:8]}"
        self.pending_approvals[approval_id] = fut

        from core.collaboration.presence import presence_manager

        try:
            await presence_manager.broadcast(
                session_id,
                {
                    "event": "path_escalation_proposal",
                    "sessionId": session_id,
                    "data": {
                        "path": path,
                        "reason": reason,
                        "approvalId": approval_id,
                    },
                },
            )
            # Wait for user input to resolve this request
            approved = await asyncio.wait_for(fut, timeout=300.0)
            if approved:
                if session_id not in self.dynamic_grants:
                    self.dynamic_grants[session_id] = set()
                self.dynamic_grants[session_id].add(path)
                self._save_grants()
                await record_decision(
                    "governance_escalation",
                    "access_granted",
                    path,
                    f"Session {session_id} granted dynamic access by user. Reason: {reason}",
                )
            else:
                log.warning("governance.escalation_denied_by_user", session=session_id, path=path)
            return approved
        except TimeoutError:
            log.warning("governance.proposal_timeout", session=session_id, path=path)
            return False
        finally:
            self.pending_approvals.pop(approval_id, None)

    def is_authorized(self, task_id: str, path: str) -> bool:
        """Checks if a path is authorized for a specific task."""
        from api.routes.files import untaint_str
        clean_path = untaint_str(path)

        from core.mcp.tools.filesystem import get_workspace_root
        ws_root = get_workspace_root()

        try:
            abs_path = Path(ws_root / clean_path).resolve()
        except Exception:
            abs_path = Path(clean_path).resolve()

        # Primary check: ContextVar workspace root
        try:
            abs_ws_root = ws_root.resolve()
            if abs_path.is_relative_to(abs_ws_root):
                return True
        except Exception:
            pass

        # Fallback: Check WORKSPACE_PATH env var
        workspace_path = os.environ.get("WORKSPACE_PATH")
        if workspace_path:
            try:
                abs_workspace = Path(workspace_path).resolve()
                if abs_path.is_relative_to(abs_workspace):
                    return True
            except Exception:
                pass

        # Check dynamic grants
        grants = self.dynamic_grants.get(task_id, set())
        for granted_path in grants:
            clean_grant = untaint_str(granted_path)
            try:
                abs_granted = Path(ws_root / clean_grant).resolve()
            except Exception:
                abs_granted = Path(clean_grant).resolve()
            
            try:
                if abs_path.is_relative_to(abs_granted):
                    return True
            except Exception:
                pass

        return False

    def resolve_approval(self, approval_id: str, approved: bool):
        """Resolves a pending user approval."""
        if fut := self.pending_approvals.get(approval_id):
            if not fut.done():
                fut.set_result(approved)


governance_manager = GovernanceManager()
