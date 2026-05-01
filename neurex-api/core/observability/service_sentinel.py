"""
core/observability/sentinel.py
Autonomous self-healing service for Neurex. Monitors port health and auto-restarts 
failed background services.
"""
from __future__ import annotations
import asyncio
import socket
import subprocess
import structlog
import os
from pathlib import Path

log = structlog.get_logger()

SERVICES = {
    "api":    {"port": 8000, "restart_cmd": "make dev-api"},
    "web":    {"port": 3000, "restart_cmd": "make dev-web"},
    "ollama": {"port": 11434, "restart_cmd": "docker compose up -d ollama"},
}

class Sentinel:
    def __init__(self, check_interval: int = 30):
        self.check_interval = check_interval
        self._running = False
        self.workspace = Path(os.getenv("WORKSPACE_PATH", "/workspace"))

    async def start(self):
        self._running = True
        log.info("sentinel.started", interval=self.check_interval)
        asyncio.create_task(self._monitor_loop())

    async def stop(self):
        self._running = False
        log.info("sentinel.stopped")

    async def _monitor_loop(self):
        while self._running:
            for name, config in SERVICES.items():
                port = config["port"]
                if not self._is_port_open(port):
                    log.warning("sentinel.service_down", service=name, port=port)
                    await self._restart_service(name, config["restart_cmd"])
                else:
                    log.debug("sentinel.service_ok", service=name, port=port)
            
            await asyncio.sleep(self.check_interval)

    def _is_port_open(self, port: int) -> bool:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.settimeout(1)
            try:
                # We check localhost for internal services
                s.connect(("127.0.0.1", port))
                return True
            except (ConnectionRefusedError, socket.timeout):
                return False

    async def _restart_service(self, name: str, cmd: str):
        log.info("sentinel.attempting_restart", service=name, command=cmd)
        try:
            # Run restart command in a separate process group
            # We use subprocess.Popen to avoid blocking the Sentinel loop
            process = subprocess.Popen(
                cmd.split(),
                cwd=self.workspace,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                start_new_session=True
            )
            log.info("sentinel.restart_initiated", service=name, pid=process.pid)
        except Exception as e:
            log.error("sentinel.restart_failed", service=name, error=str(e))

sentinel = Sentinel()
