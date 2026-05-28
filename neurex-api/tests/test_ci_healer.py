"""
tests/test_ci_healer.py
Tests for CIHealer Gitea Actions API polling and SQLite task queuing.
"""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from sqlmodel import select

from core.observability.ci_healer import CIHealer
from core.settings.manager import settings_manager
from core.task_graph import TaskNode, TaskStatus


@pytest.mark.asyncio
async def test_ci_healer_skips_when_not_configured():
    """CIHealer must skip polling if Gitea environment is not configured."""
    with (
        patch.object(settings_manager, "get", return_value=None),
        patch("httpx.AsyncClient.get", new_callable=AsyncMock) as mock_get,
    ):
        healer = CIHealer()
        result = await healer._fetch_latest_failure()
        assert result is None
        mock_get.assert_not_called()


@pytest.mark.asyncio
async def test_ci_healer_polls_and_finds_failure_and_queues_task(db_session):
    """CIHealer must fetch failed runs/jobs/logs and queue an orchestrator task."""

    def mock_get_setting(key):
        if key == "gitea_base_url":
            return "http://mock-gitea.local"
        if key == "gitea_token":
            return "mock-token"
        if key == "gitea_owner":
            return "mock-owner"
        if key == "gitea_repo":
            return "mock-repo"
        return None

    mock_runs_response = [
        {
            "id": 42,
            "status": "completed",
            "conclusion": "failure",
            "head_branch": "feature-branch",
            "head_sha": "abc123sha",
        }
    ]

    mock_jobs_response = [
        {
            "id": 101,
            "name": "build-and-test",
            "conclusion": "failure",
        }
    ]

    mock_log_text = "AssertionError: test_something failed"

    mock_runs_resp = MagicMock()
    mock_runs_resp.status_code = 200
    mock_runs_resp.json = MagicMock(return_value=mock_runs_response)

    mock_jobs_resp = MagicMock()
    mock_jobs_resp.status_code = 200
    mock_jobs_resp.json = MagicMock(return_value=mock_jobs_response)

    mock_logs_resp = MagicMock()
    mock_logs_resp.status_code = 200
    mock_logs_resp.text = mock_log_text

    async def mock_client_get(url, *args, **kwargs):
        if url.endswith("/actions/runs"):
            return mock_runs_resp
        if url.endswith("/runs/42/jobs"):
            return mock_jobs_resp
        if url.endswith("/jobs/101/logs"):
            return mock_logs_resp
        return MagicMock(status_code=404)

    healer = CIHealer()

    with (
        patch.object(settings_manager, "get", side_effect=mock_get_setting),
        patch("httpx.AsyncClient.get", side_effect=mock_client_get),
        patch("core.observability.ci_healer.async_session", return_value=db_session),
    ):
        # 1. Fetch latest failure
        failure = await healer._fetch_latest_failure()
        assert failure is not None
        assert failure["id"] == 42
        assert failure["repo"] == "mock-owner/mock-repo"
        assert failure["job_name"] == "build-and-test"
        assert failure["log"] == mock_log_text

        # 2. Initiate healing (queues the task in DB)
        await healer.initiate_healing(failure)
        assert 42 in healer.processed_runs

        # Verify task is queued in SQLite
        statement = select(TaskNode).where(TaskNode.agent_type == "orchestrator")
        results = await db_session.exec(statement)
        task = results.first()
        assert task is not None
        assert "CI Self-Healing: mock-owner/mock-repo" in task.title
        assert "Run #42" in task.description
        assert "AssertionError: test_something failed" in task.description
        assert task.status == TaskStatus.PENDING

        # 3. Next poll should skip because run ID 42 is in processed_runs
        failure_again = await healer._fetch_latest_failure()
        assert failure_again is None
