import asyncio
import os
from unittest.mock import AsyncMock, patch

import pytest

from core.security.governance import GovernanceManager


@pytest.fixture
def mock_workspace(tmp_path):
    ws = tmp_path / "workspace"
    ws.mkdir()
    os.environ["WORKSPACE_PATH"] = str(ws)
    return ws

@pytest.fixture
def gov(mock_workspace, tmp_path):
    # Use a clean governance manager with a test grants file
    with patch("core.security.governance.get_grants_file") as mock_get_grants:
        mock_get_grants.return_value = tmp_path / ".neurex" / "grants.json"
        g = GovernanceManager()
        g.dynamic_grants = {}
        return g

def test_is_authorized_safe_path(gov, mock_workspace):
    assert gov.is_authorized("test_task", str(mock_workspace / "safe_file.txt")) is True

def test_is_authorized_traversal_blocked(gov, mock_workspace):
    # Attempt to traverse up out of the workspace
    traversal_path = str(mock_workspace / ".." / "etc" / "passwd")
    assert gov.is_authorized("test_task", traversal_path) is False

def test_is_authorized_partial_path_blocked(gov, mock_workspace, tmp_path):
    # E.g. workspace is /tmp/workspace, attacker tries /tmp/workspace_evil
    evil_ws = tmp_path / "workspace_evil"
    evil_ws.mkdir()
    evil_file = str(evil_ws / "secret.txt")
    # This would pass a naïve .startswith(workspace) if workspace lacked trailing slash!
    assert gov.is_authorized("test_task", evil_file) is False

@pytest.mark.asyncio
async def test_request_escalation_approved(gov):
    session_id = "test_session"
    path = "/etc/passwd"
    
    with patch("core.collaboration.presence.presence_manager.broadcast", new_callable=AsyncMock) as mock_broadcast:
        # Schedule a background task to resolve the future after a small delay
        async def mock_user_approve():
            await asyncio.sleep(0.01)
            # Find the approval ID
            assert len(gov.pending_approvals) == 1
            approval_id = list(gov.pending_approvals.keys())[0]
            gov.resolve_approval(approval_id, True)

        asyncio.create_task(mock_user_approve())

        approved = await gov.request_escalation(session_id, path, "need it")
        
        assert approved is True
        assert path in gov.dynamic_grants[session_id]
        
        # Verify broadcast was called
        mock_broadcast.assert_called_once()
        args, kwargs = mock_broadcast.call_args
        assert args[0] == session_id
        assert args[1]["event"] == "path_escalation_proposal"

@pytest.mark.asyncio
async def test_request_escalation_denied(gov):
    session_id = "test_session"
    path = "/etc/shadow"
    
    with patch("core.collaboration.presence.presence_manager.broadcast", new_callable=AsyncMock) as mock_broadcast:
        async def mock_user_deny():
            await asyncio.sleep(0.01)
            approval_id = list(gov.pending_approvals.keys())[0]
            gov.resolve_approval(approval_id, False)

        asyncio.create_task(mock_user_deny())

        approved = await gov.request_escalation(session_id, path, "evil")
        
        assert approved is False
        assert session_id not in gov.dynamic_grants or path not in gov.dynamic_grants.get(session_id, set())

def test_dynamic_grant_authorizes_path(gov, mock_workspace):
    session_id = "test_session"
    outside_path = "/tmp/outside_file.txt"
    
    assert gov.is_authorized(session_id, outside_path) is False
    
    gov.dynamic_grants[session_id] = {outside_path}
    
    assert gov.is_authorized(session_id, outside_path) is True
