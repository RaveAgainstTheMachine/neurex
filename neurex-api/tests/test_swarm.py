"""
Unit tests for the Swarm Engine.
"""

from __future__ import annotations

from core.agents.swarm_engine import SwarmEngine


def test_swarm_engine_aggregation(tmp_path):
    # Setup mock workspace
    workspace = tmp_path / "workspace"
    workspace.mkdir()

    file_a = workspace / "file_a.py"
    file_a.write_text("print('original file_a')", encoding="utf-8")

    swarm_eng = SwarmEngine(workspace_path=workspace)

    mutations = [
        {"path": "file_a.py", "modified": "print('modified file_a')"},
        {"path": "file_b.py", "modified": "print('new file_b')"},
    ]

    payload = swarm_eng.create_swarm_diff(task_id="task-123", mutations=mutations)

    assert payload["type"] == "swarm_diff"
    assert payload["taskId"] == "task-123"
    assert len(payload["changes"]) == 2

    # Verify file_a.py (modification)
    change_a = next(c for c in payload["changes"] if c["path"] == "file_a.py")
    assert change_a["original"] == "print('original file_a')"
    assert change_a["modified"] == "print('modified file_a')"

    # Verify file_b.py (creation)
    change_b = next(c for c in payload["changes"] if c["path"] == "file_b.py")
    assert change_b["original"] == ""
    assert change_b["modified"] == "print('new file_b')"
