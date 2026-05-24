"""
core/agents/swarm_engine.py
Orchestrator for aggregating and serializing multi-file code mutations.
Produces visual diff overlays for the frontend Swarm Diff workspace.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

import structlog

from api.routes.files import get_workspace

log = structlog.get_logger()


class SwarmEngine:
    """
    Serializes and aggregates sweeping multi-file mutations proposed by the agent swarm
    into standard JSON structures for human-in-the-loop validation.
    """

    def __init__(self, workspace_path: Path | None = None) -> None:
        try:
            resolved_path = workspace_path or get_workspace()
            self.workspace_path: Path = resolved_path if resolved_path is not None else Path.cwd()
        except Exception:
            self.workspace_path = Path.cwd()

    def create_swarm_diff(
        self,
        task_id: str,
        mutations: list[dict[str, str]],
    ) -> dict[str, Any]:
        """
        Aggregates multiple file mutations into a serialized swarm_diff payload.
        Each item in `mutations` must be a dictionary specifying:
          - "path": Relative path from the workspace root.
          - "modified": The full proposed file content (or empty string for deletions).
        """
        changes: list[dict[str, str]] = []

        for mut in mutations:
            rel_path = mut.get("path")
            modified = mut.get("modified", "")

            if not rel_path:
                log.warning("swarm_engine.missing_path", mutation=mut)
                continue

            file_abs_path = (self.workspace_path / rel_path).resolve()

            original = ""
            if file_abs_path.exists() and file_abs_path.is_file():
                try:
                    original = file_abs_path.read_text(encoding="utf-8", errors="replace")
                except Exception as e:
                    log.error("swarm_engine.read_failed", path=rel_path, error=str(e))
                    original = ""

            changes.append({
                "path": rel_path,
                "original": original,
                "modified": modified,
            })

        payload: dict[str, Any] = {
            "type": "swarm_diff",
            "taskId": task_id,
            "changes": changes,
        }

        log.info(
            "swarm_engine.swarm_diff_created",
            task_id=task_id,
            num_changes=len(changes),
        )
        return payload
