"""
core/observability/ci_healer.py
Monitors CI/CD pipelines and autonomously triggers self-healing tasks.
Integrates with the Orchestrator to fix regression bugs in the background.
"""

from __future__ import annotations

import asyncio
import uuid
from typing import Any

import httpx
import structlog

from core.settings.manager import settings_manager
from core.task_graph import TaskStatus, async_session, create_task

log = structlog.get_logger()


class CIHealer:
    def __init__(self):
        self.monitored_repos: list[str] = []
        self.healing_active = False
        self.processed_runs: set[int] = set()

    async def _fetch_latest_failure(self) -> dict[str, Any] | None:
        """
        Polls Gitea API for failed action runs.
        """
        base_url = settings_manager.get("gitea_base_url") or "http://localhost:3000"
        token = settings_manager.get("gitea_token")
        owner = settings_manager.get("gitea_owner")
        repo = settings_manager.get("gitea_repo")

        # Skip polling if not fully configured
        if not owner or not repo or not token:
            log.debug("ci_healer.gitea_not_configured")
            return None

        url = f"{base_url.rstrip('/')}/api/v1/repos/{owner}/{repo}/actions/runs"
        headers = {
            "Accept": "application/json",
            "Authorization": f"token {token}",
        }

        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(url, headers=headers)
                if response.status_code != 200:
                    log.error(
                        "ci_healer.gitea_api_error",
                        status_code=response.status_code,
                        body=response.text[:200],
                    )
                    return None

                data = response.json()
                runs = []
                if isinstance(data, list):
                    runs = data
                elif isinstance(data, dict):
                    runs = data.get("workflow_runs") or data.get("runs") or []

                if not runs:
                    return None

                for run in runs:
                    run_id = run.get("id")
                    if not run_id:
                        continue
                    if run_id in self.processed_runs:
                        continue

                    status = run.get("status")
                    conclusion = run.get("conclusion")

                    if status == "completed" and conclusion == "failure":
                        log_content = "Unknown job execution error"
                        job_name = "unknown"

                        # Retrieve jobs for this run to locate details
                        jobs_url = f"{base_url.rstrip('/')}/api/v1/repos/{owner}/{repo}/actions/runs/{run_id}/jobs"
                        jobs_resp = await client.get(jobs_url, headers=headers)
                        if jobs_resp.status_code == 200:
                            jobs_data = jobs_resp.json()
                            jobs = []
                            if isinstance(jobs_data, list):
                                jobs = jobs_data
                            elif isinstance(jobs_data, dict):
                                jobs = jobs_data.get("jobs") or []

                            for job in jobs:
                                if job.get("conclusion") == "failure":
                                    job_id = job.get("id")
                                    job_name = job.get("name", "unknown")

                                    # Try retrieving logs from standard Gitea path
                                    logs_url = f"{base_url.rstrip('/')}/api/v1/repos/{owner}/{repo}/actions/runs/jobs/{job_id}/logs"
                                    logs_resp = await client.get(logs_url, headers=headers)
                                    if logs_resp.status_code == 200:
                                        log_content = logs_resp.text
                                    else:
                                        # Try alternate path
                                        alt_logs_url = f"{base_url.rstrip('/')}/api/v1/repos/{owner}/{repo}/actions/jobs/{job_id}/logs"
                                        alt_logs_resp = await client.get(
                                            alt_logs_url, headers=headers
                                        )
                                        if alt_logs_resp.status_code == 200:
                                            log_content = alt_logs_resp.text
                                    break

                        return {
                            "id": run_id,
                            "repo": f"{owner}/{repo}",
                            "branch": run.get("head_branch", "main"),
                            "sha": run.get("head_sha", ""),
                            "job_name": job_name,
                            "log": log_content,
                        }
        except Exception as e:
            log.exception("ci_healer.poll_exception", error=str(e))

        return None

    async def check_pipeline_health(self):
        """
        Polls CI providers (Gitea Actions) for failed builds.
        """
        log.info("ci_healer.monitoring_started")
        while True:
            failed_build = await self._fetch_latest_failure()

            if failed_build:
                await self.initiate_healing(failed_build)

            await asyncio.sleep(300)  # Poll every 5 minutes

    async def initiate_healing(self, failure_data: dict[str, Any]):
        """
        Launches a background Orchestrator task to resolve the CI failure.
        """
        repo = failure_data.get("repo")
        error_log = failure_data.get("log", "Unknown error")
        run_id = failure_data.get("id")

        log.warning("ci_healer.failure_detected", repo=repo, error=error_log[:100])

        if run_id:
            self.processed_runs.add(run_id)

        try:
            async with async_session() as session:
                await create_task(
                    session=session,
                    graph_id=str(uuid.uuid4()),
                    agent_type="orchestrator",
                    title=f"CI Self-Healing: {repo}",
                    description=(
                        f"Automatically resolve CI failure on {repo} (Run #{run_id}). "
                        f"Job: {failure_data.get('job_name')}. "
                        f"Error log preview: {error_log[:500]}"
                    ),
                    status=TaskStatus.PENDING,
                )
            log.info("ci_healer.healing_task_queued", repo=repo, run_id=run_id)
        except Exception as e:
            log.error("ci_healer.healing_task_queue_failed", repo=repo, error=str(e))


ci_healer = CIHealer()
