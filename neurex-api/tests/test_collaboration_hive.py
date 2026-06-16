from unittest.mock import AsyncMock, patch

import pytest

from core.collaboration.hive_manager import HiveManager


@pytest.mark.asyncio
async def test_hive_manager_workflow():
    manager = HiveManager()

    blueprint = {
        "steps": [
            {"target_paths": ["src/a.py"], "action": "edit"},
            {"target_paths": ["src/b.py", "src/a.py"], "action": "test"} # Conflict path with step 1
        ]
    }

    # Mock record_decision & global_memory pointer
    with patch("core.collaboration.hive_manager.record_decision", new_callable=AsyncMock) as mock_record:
        with patch("core.collaboration.hive_manager.global_memory.add_pointer", new_callable=AsyncMock) as mock_add_pointer:
            
            # Shard the blueprint
            shards = await manager.shard_blueprint("bp1", blueprint)
            assert len(shards) == 2
            assert shards[0]["shard_id"] == "bp1_s0"
            mock_record.assert_called_once()

            # Claim first shard
            claimed = await manager.claim_shard("task_1", "bp1_s0")
            assert claimed is True
            assert manager.path_locks["src/a.py"] == "task_1"
            assert manager.shards_by_id["bp1_s0"]["status"] == "executing"
            mock_add_pointer.assert_called_once()

            # Attempt to claim second shard (should fail because src/a.py is locked by task_1)
            claimed_conflict = await manager.claim_shard("task_2", "bp1_s1")
            assert claimed_conflict is False

            # Claim with non-existent shard should return False
            claimed_none = await manager.claim_shard("task_2", "non_existent_shard")
            assert claimed_none is False

            # Release first shard
            manager.release_shard("task_1", "bp1_s0")
            assert "src/a.py" not in manager.path_locks
            assert manager.shards_by_id["bp1_s0"]["status"] == "completed"

            # Now claim second shard (should succeed)
            claimed_now = await manager.claim_shard("task_2", "bp1_s1")
            assert claimed_now is True
            assert manager.path_locks["src/a.py"] == "task_2"
            assert manager.path_locks["src/b.py"] == "task_2"
