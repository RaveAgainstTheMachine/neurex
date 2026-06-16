"""
tests/test_reliability.py
Unit and integration tests for v0.6.0 Reliability, Evals & Controls features:
1. Startup dependency audit.
2. Zero-Diff Staging Guard (filesystem tools & API endpoints).
3. Teleplay Replay chronological screenplay endpoints.
"""

import shutil
from pathlib import Path

import pytest

from core.mcp.tools.filesystem import (
    apply_diff,
    commit_staging,
    delete_file,
    list_staging,
    write_file,
)
from core.observability.dependency_watch import dependency_watch
from core.observability.flight_recorder import get_flight_log, record_decision


@pytest.fixture(autouse=True)
def clean_test_workspace():
    """Ensure the test workspace is completely fresh before and after every test."""
    workspace_path = Path("/tmp/neurex-test-workspace")
    import os
    os.environ["WORKSPACE_PATH"] = str(workspace_path)
    if workspace_path.exists():
        shutil.rmtree(workspace_path)
    workspace_path.mkdir(parents=True, exist_ok=True)
    yield
    if workspace_path.exists():
        shutil.rmtree(workspace_path)


@pytest.mark.asyncio
async def test_run_local_audit(db_session):
    """Verify that run_local_audit runs pip list --outdated and logs decision traces to FlightRecorder."""
    # Clear the flight recorder buffers/tables or just look for the specific system-watch event
    from core.observability.flight_recorder import _BUFFER_LOCK, _DECISION_BUFFER

    async with _BUFFER_LOCK:
        _DECISION_BUFFER.clear()

    # Trigger the dependency startup audit
    await dependency_watch.run_local_audit()

    # Retrieve reasoning traces including pending buffer items
    events = await get_flight_log("system-watch")

    assert len(events) >= 1
    audit_event = [e for e in events if e.get("task_id") == "dependency-startup-audit"][0]
    assert audit_event["agent_type"] == "dependency"
    assert audit_event["decision"] == "Dependency Audit"
    assert any(
        x in audit_event["rationale"].lower()
        for x in ["outdated", "up-to-date", "failed", "executing"]
    )


@pytest.mark.asyncio
async def test_zero_diff_staging_guard_tools(db_session):
    """Verify that filesystem write, delete, and diff apply operations correctly target the staging directory in staging mode."""
    workspace = Path("/tmp/neurex-test-workspace")
    staging_root = workspace / ".neurex" / "staging"

    # 1. Write file in staging mode
    res = await write_file("app.py", "print('hello')", autonomy_level="staging")
    assert "OK" in res

    # Original should not exist
    assert not (workspace / "app.py").exists()
    # Staged file should exist
    assert (staging_root / "app.py").exists()
    assert (staging_root / "app.py").read_text() == "print('hello')"

    # 2. Apply diff in staging mode
    res_diff = await apply_diff(
        path="app.py",
        search="print('hello')",
        replace="print('hello world')",
        autonomy_level="staging",
    )
    assert "OK" in res_diff
    # Original should still not exist
    assert not (workspace / "app.py").exists()
    # Staged file should have updated content
    assert (staging_root / "app.py").read_text() == "print('hello world')"

    # 3. List staging
    staged_items = await list_staging()
    assert len(staged_items) == 1
    assert staged_items[0]["path"] == "app.py"
    assert staged_items[0]["status"] == "modified"

    # 4. Commit staging
    commit_res = await commit_staging()
    assert commit_res["committed_count"] == 1
    # Original should now exist with committed content
    assert (workspace / "app.py").exists()
    assert (workspace / "app.py").read_text() == "print('hello world')"
    # Staging should be cleared
    assert not (staging_root / "app.py").exists()
    assert len(await list_staging()) == 0

    # 5. Delete file in staging mode
    res_del = await delete_file("app.py", autonomy_level="staging")
    assert "OK" in res_del
    # Original should still exist (deletion is staged, not committed)
    assert (workspace / "app.py").exists()
    # Staged deletion marker should exist
    assert (staging_root / "app.py.deleted").exists()

    # List staging shows deleted status
    staged_items_del = await list_staging()
    assert len(staged_items_del) == 1
    assert staged_items_del[0]["path"] == "app.py"
    assert staged_items_del[0]["status"] == "deleted"

    # Commit deletion
    commit_del_res = await commit_staging()
    assert commit_del_res["committed_count"] == 1
    # Original should be deleted
    assert not (workspace / "app.py").exists()
    # Staged marker should be cleared
    assert not (staging_root / "app.py.deleted").exists()


@pytest.mark.asyncio
async def test_staging_api_endpoints(test_client, db_session):
    """Verify that stage routes list, commit, and clear staging files through HTTP API."""
    workspace = Path("/tmp/neurex-test-workspace")
    staging_root = workspace / ".neurex" / "staging"

    # Pre-populate workspace with an original file to be deleted in staging
    await write_file("deleteme.txt", "original content", autonomy_level="limited")

    # Propose file creation and deletion in staging
    await write_file("config.json", '{"theme": "dark"}', autonomy_level="staging")
    await delete_file("deleteme.txt", autonomy_level="staging")

    # GET /api/files/stage
    get_res = await test_client.get("/api/files/stage")
    assert get_res.status_code == 200
    staged_items = get_res.json()
    assert len(staged_items) == 2

    paths = {item["path"]: item["status"] for item in staged_items}
    assert "config.json" in paths
    assert paths["config.json"] == "modified"
    assert "deleteme.txt" in paths
    assert paths["deleteme.txt"] == "deleted"

    # POST /api/files/stage/clear
    clear_res = await test_client.post("/api/files/stage/clear")
    assert clear_res.status_code == 200
    assert clear_res.json()["status"] == "ok"

    # Staged items should be empty now
    get_res_empty = await test_client.get("/api/files/stage")
    assert len(get_res_empty.json()) == 0

    # Repopulate and Commit via API
    await write_file("main.py", "def run(): pass", autonomy_level="staging")
    commit_res = await test_client.post("/api/files/stage/commit")
    assert commit_res.status_code == 200
    assert commit_res.json()["committed_count"] == 1

    # Original file must exist in workspace
    assert (workspace / "main.py").exists()
    assert (workspace / "main.py").read_text() == "def run(): pass"


@pytest.mark.asyncio
async def test_teleplay_replay_endpoint(test_client, db_session):
    """Verify that GET /api/observability/replay/{conversation_id} returns chronological screenplay beats."""
    conversation_id = "test-session-123"

    from core.observability.flight_recorder import _BUFFER_LOCK, _DECISION_BUFFER

    async with _BUFFER_LOCK:
        _DECISION_BUFFER.clear()

    # Record some mock decisions using record_decision
    await record_decision(
        conversation_id=conversation_id,
        agent_type="planner",
        decision="Create Plan",
        rationale="Analyzing workspace structural health",
        task_id="task-1",
        context_keys=["files", "git"],
    )

    await record_decision(
        conversation_id=conversation_id,
        agent_type="coder",
        decision="Write Test",
        rationale="Implementing safety test suite",
        task_id="task-2",
        context_keys=["test_file"],
    )

    # GET /api/observability/replay/{conversation_id}
    response = await test_client.get(f"/api/observability/replay/{conversation_id}")
    assert response.status_code == 200
    beats = response.json()

    assert len(beats) == 2

    # Chronological sort means "Create Plan" is first
    assert beats[0]["beat_number"] == 1
    assert beats[0]["agent_type"] == "planner"
    assert beats[0]["act"] == "Create Plan"
    assert beats[0]["narrative"] == "Analyzing workspace structural health"
    assert beats[0]["context_metadata"] == ["files", "git"]
    assert "timestamp" in beats[0]

    assert beats[1]["beat_number"] == 2
    assert beats[1]["agent_type"] == "coder"
    assert beats[1]["act"] == "Write Test"
    assert beats[1]["narrative"] == "Implementing safety test suite"
    assert beats[1]["context_metadata"] == ["test_file"]
