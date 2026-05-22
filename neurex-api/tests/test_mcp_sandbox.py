"""
tests/test_mcp_sandbox.py
Tests for MCP Visual Sandbox & Permissions routing system.
"""

from __future__ import annotations

import pytest
from sqlmodel import select

from core.mcp.client import get_tool_permission
from core.task_graph import MCPToolPermission


@pytest.fixture(autouse=True)
def override_auth():
    from api.routes.auth import get_current_user
    from core.task_graph import User, UserRole
    from main import app

    mock_user = User(username="test_admin", role=UserRole.ADMIN)

    async def mock_get_current_user():
        return mock_user

    app.dependency_overrides[get_current_user] = mock_get_current_user
    yield
    app.dependency_overrides.clear()


@pytest.mark.asyncio

async def test_list_mcp_servers(test_client):
    """GET /api/mcp/servers must return list of virtual and dynamic servers with tools and schemas."""
    response = await test_client.get("/api/mcp/servers")
    assert response.status_code == 200
    servers = response.json()
    assert len(servers) > 0

    # Ensure Core Virtual servers exist (e.g. Filesystem Substrate)
    filesystem_server = next((s for s in servers if s["name"] == "Filesystem Substrate"), None)
    assert filesystem_server is not None
    assert filesystem_server["type"] == "core"
    assert len(filesystem_server["tools"]) > 0

    # Verify a specific tool (e.g. read_file) and its extracted schema details
    read_tool = next((t for t in filesystem_server["tools"] if t["name"] == "read_file"), None)
    assert read_tool is not None
    assert "description" in read_tool
    assert "inputSchema" in read_tool
    assert "rule" in read_tool


@pytest.mark.asyncio
async def test_update_permission_rule(test_client, db_session):
    """POST /api/mcp/permissions must set granular permission rules in SQLite and override defaults."""
    # 1. Default for write_file is 'ask'
    initial_perm = await get_tool_permission("write_file")
    assert initial_perm == "ask"

    # 2. Update rule to 'allow' via API
    payload = {"tool_name": "write_file", "rule": "allow"}
    response = await test_client.post("/api/mcp/permissions", json=payload)
    assert response.status_code == 200
    assert response.json()["status"] == "success"

    # 3. Verify database reflects 'allow'
    result = await db_session.exec(
        select(MCPToolPermission).where(MCPToolPermission.tool_name == "write_file")
    )
    db_perm = result.first()
    assert db_perm is not None
    assert db_perm.rule == "allow"

    # 4. Verify helper functions load correct rules
    updated_perm = await get_tool_permission("write_file")
    assert updated_perm == "allow"


@pytest.mark.asyncio
async def test_run_playground_tool(test_client):
    """POST /api/mcp/playground/run should execute tools manually and return raw outputs."""
    # Run a simple read-only tool like list_directory
    payload = {
        "tool_name": "list_directory",
        "arguments": {"path": "."}
    }
    response = await test_client.post("/api/mcp/playground/run", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "success"
    assert "result" in data
