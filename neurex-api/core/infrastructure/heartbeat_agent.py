"""
core/infrastructure/heartbeat_agent.py
Standalone heartbeat agent for RPC Node deployments.

Runs as a lightweight process (no full API server required) and broadcasts
this node's compute capabilities to the Master every 15 seconds.
The Master's MeshRouter uses this data for weighted-load routing.

Usage (via docker-compose.node.yml):
    python -m core.infrastructure.heartbeat_agent
"""
import asyncio
import os
import socket
import structlog
import httpx
import psutil

log = structlog.get_logger()

# ── Config from environment ────────────────────────────────────────────────────
MASTER_URL   = os.getenv("MASTER_URL", "http://localhost:8080")
MASTER_TOKEN = os.getenv("MASTER_TOKEN", "")
NODE_NAME    = os.getenv("NODE_NAME", socket.gethostname())
BIND_IP      = os.getenv("BIND_IP", "0.0.0.0")
RPC_PORT     = int(os.getenv("RPC_PORT", "50051"))
INTERVAL_S   = 15  # heartbeat cadence in seconds


def get_local_ip() -> str:
    """Resolve the routable local IP for the Master to call back to."""
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except Exception:
        return BIND_IP if BIND_IP != "0.0.0.0" else "127.0.0.1"


def get_system_metrics() -> dict:
    """Collect real-time hardware telemetry."""
    mem = psutil.virtual_memory()
    metrics = {
        "cpu_percent": psutil.cpu_percent(interval=1),
        "ram_total_gb": round(mem.total / (1024 ** 3), 2),
        "ram_used_gb":  round(mem.used  / (1024 ** 3), 2),
        "vram_gb": 0.0,
    }

    # Attempt NVIDIA VRAM detection
    try:
        import subprocess
        result = subprocess.check_output(
            ["nvidia-smi", "--query-gpu=memory.free", "--format=csv,noheader,nounits"],
            timeout=3, text=True
        ).strip()
        free_mib = sum(int(x) for x in result.splitlines() if x.strip().isdigit())
        metrics["vram_gb"] = round(free_mib / 1024, 2)
    except Exception:
        pass

    return metrics


async def send_heartbeat(client: httpx.AsyncClient, local_ip: str) -> None:
    """POST this node's capabilities to the Master's presence endpoint."""
    metrics = get_system_metrics()

    payload = {
        "node_name": NODE_NAME,
        "role": "node",
        "rpc_endpoint": f"{local_ip}:{RPC_PORT}",
        "metrics": metrics,
        "is_rpc_worker": True,
    }

    try:
        resp = await client.post(
            f"{MASTER_URL}/api/infra/presence/heartbeat",
            json=payload,
            headers={"Authorization": f"Bearer {MASTER_TOKEN}"},
            timeout=5,
        )
        resp.raise_for_status()
        log.info(
            "heartbeat.sent",
            node=NODE_NAME,
            rpc=f"{local_ip}:{RPC_PORT}",
            vram=metrics["vram_gb"],
            cpu=metrics["cpu_percent"],
        )
    except httpx.HTTPStatusError as e:
        log.warning("heartbeat.rejected", status=e.response.status_code)
    except Exception as e:
        log.warning("heartbeat.failed", error=str(e))


async def main():
    log.info("heartbeat_agent.starting", node=NODE_NAME, master=MASTER_URL)
    local_ip = get_local_ip()
    log.info("heartbeat_agent.identity", local_ip=local_ip, rpc_port=RPC_PORT)

    async with httpx.AsyncClient() as client:
        while True:
            await send_heartbeat(client, local_ip)
            await asyncio.sleep(INTERVAL_S)


if __name__ == "__main__":
    asyncio.run(main())
