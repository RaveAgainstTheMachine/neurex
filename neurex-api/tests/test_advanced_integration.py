"""
neurex-api/tests/test_advanced_integration.py
Universal Advanced Integration Tests for:
1. Distributed peer-to-peer mesh discoverability and VRAM sharing
2. ChromaDB AST parsing / memory hive mind indexing accuracy
3. Security Sentinel vulnerability detection threats logging
"""

import asyncio
import os
from unittest.mock import AsyncMock, patch

import pytest

from core.infrastructure.mesh import MeshRouter
from core.infrastructure.vram_pool import VirtualVRAMPool
from core.memory.hive import HiveMind
from core.security.sentinel import SecuritySentinel


@pytest.mark.asyncio
async def test_p2p_mesh_load_balancing_and_vram_pooling(tmp_path):
    """Verify MeshRouter peer routing capability matching predictive resource loads and VirtualVRAMPool allocations."""
    # 1. Initialize MeshRouter
    with patch("core.infrastructure.mesh.PEERS_FILE", tmp_path / "mesh_peers.json"):
        with patch("core.infrastructure.mesh.MeshRouter.check_health", return_value=None):
            router = MeshRouter()

        # Add peer 1: High VRAM, low latency, low load
        peer1_url = "http://192.168.1.100:3000"
        router.add_peer(peer1_url, "token-1", "GPU-Node-Alpha")
        router.peers[peer1_url].status = "online"
        router.peers[peer1_url].vram_gb = 24.0
        router.peers[peer1_url].latency_ms = 5
        router.peers[peer1_url].cpu_percent = 10.0
        router.peers[peer1_url].models = ["qwen2.5-coder:7b"]

        # Add peer 2: Lower VRAM, higher latency, overloaded
        peer2_url = "http://192.168.1.101:3000"
        router.add_peer(peer2_url, "token-2", "GPU-Node-Beta")
        router.peers[peer2_url].status = "online"
        router.peers[peer2_url].vram_gb = 8.0
        router.peers[peer2_url].latency_ms = 120
        router.peers[peer2_url].cpu_percent = 90.0
        router.peers[peer2_url].queue_depth = 4

        # Add peer 3: Offline node (should be completely excluded)
        peer3_url = "http://192.168.1.102:3000"
        router.add_peer(peer3_url, "token-3", "Offline-Node")
        router.peers[peer3_url].status = "offline"

        # Mock local node metrics
        with patch("core.infrastructure.manager.infrastructure_manager.get_system_metrics", return_value={"vram_gb": 8.0, "cpu_percent": 15.0}):
            with patch("core.infrastructure.manager.infrastructure_manager.get_installed_models", new_callable=AsyncMock, return_value=[]):
                # Request a model; router should select GPU-Node-Alpha (high VRAM, low load)
                best_node = await router.get_best_inference_node(model_name="qwen2.5-coder:7b")
                assert "ollama_proxy" in best_node
                assert peer1_url in best_node

    # 2. Test VRAM pool resource aggregation and sharded capacity allocations
    pool = VirtualVRAMPool()
    with patch("core.infrastructure.mesh.mesh_router", router):
        with patch("core.infrastructure.vram_pool.mesh_router", router):
            with patch("core.infrastructure.manager.InfrastructureManager.get_system_vram", return_value=8.0):
                await pool.synchronize_mesh_resources()

                # Local node (8GB) + GPU-Node-Alpha (24GB) + GPU-Node-Beta (8GB) = 40GB
                assert pool.total_capacity_gb == 40.0
            assert len(pool.shards) == 3

            # Allocate 30GB of VRAM (should succeed using alpha and beta/local shards)
            plan = pool.allocate_vram(30.0)
            assert plan is not None
            assert len(plan) >= 2
            assert sum(item["allocated_gb"] for item in plan) == 30.0

            # Release allocations back to unified pool
            pool.release_vram(plan)
            for shard in pool.shards.values():
                assert shard.used_gb == 0.0


def test_chromadb_ast_chunk_memory_hive(tmp_path):
    """Test ChromaDB context remember and recall capability under high-fidelity AST semantic chunks."""
    os.environ["CHROMA_DB_DIR"] = str(tmp_path / "chroma_hive")
    with patch("core.memory.hive.CHROMA_PATH", str(tmp_path / "chroma_hive")):
        hive = HiveMind()

        # Inject context fragments
        doc_id_1 = "ast_chunk_1"
        content_1 = "def execute_sql(query: str):\n    '''Executes privileged SQL substrate query'''\n    return db.execute(query)"
        meta_1 = {"language": "python", "component": "MCPSandbox", "type": "function"}

        doc_id_2 = "ast_chunk_2"
        content_2 = "class DebateSteering:\n    '''Manages interactive agent consensus and steer inputs'''\n    pass"
        meta_2 = {"language": "python", "component": "DebateSwarm", "type": "class"}

        hive.remember(content_1, meta_1, doc_id_1)
        hive.remember(content_2, meta_2, doc_id_2)

        # Recall by query text similarity
        recalled = hive.recall(query="privileged database execution commands")
        assert len(recalled) > 0
        
        # Verify the database execution snippet is returned
        best_match = recalled[0]
        assert "execute_sql" in best_match["content"]
        assert best_match["metadata"]["component"] == "MCPSandbox"


def test_security_sentinel_threats_auditing(tmp_path):
    """Verify that SecuritySentinel background engine parses AST trees and reports insecure coding patterns."""
    sentinel = SecuritySentinel(workspace_path=str(tmp_path))

    # 1. Create a safe python file
    safe_code = "def get_sum(a, b):\n    return a + b\n"
    with open(tmp_path / "safe.py", "w") as f:
        f.write(safe_code)

    # 2. Create insecure files containing critical threats
    eval_code = "result = eval(input('Enter equation: '))\n"
    with open(tmp_path / "unsafe_eval.py", "w") as f:
        f.write(eval_code)

    insecure_subp_code = "import subprocess\nsubprocess.run('ls -la', shell=True)\n"
    with open(tmp_path / "unsafe_subp.py", "w") as f:
        f.write(insecure_subp_code)

    insecure_os_code = "import os\nos.system('rm -rf /tmp/scratch')\n"
    with open(tmp_path / "unsafe_os.py", "w") as f:
        f.write(insecure_os_code)

    # Scan and verify threat detection details
    safe_issues = sentinel.scan_file("safe.py")
    assert len(safe_issues) == 0

    eval_issues = sentinel.scan_file("unsafe_eval.py")
    assert len(eval_issues) == 1
    assert eval_issues[0]["type"] == "DYNAMIC_EXECUTION"
    assert eval_issues[0]["severity"] == "CRITICAL"

    subp_issues = sentinel.scan_file("unsafe_subp.py")
    assert len(subp_issues) == 1
    assert subp_issues[0]["type"] == "INSECURE_SUBPROCESS"
    assert subp_issues[0]["severity"] == "CRITICAL"

    os_issues = sentinel.scan_file("unsafe_os.py")
    assert len(os_issues) == 1
    assert os_issues[0]["type"] == "INSECURE_OS_SYSTEM"
    assert os_issues[0]["severity"] == "HIGH"

    # Verify background workspace audit report returns correct stats
    report = asyncio.run(sentinel.audit_workspace())
    assert report["status"] == "success"
    assert len(report["issues"]) == 3  # unsafe_eval, unsafe_subp, unsafe_os
