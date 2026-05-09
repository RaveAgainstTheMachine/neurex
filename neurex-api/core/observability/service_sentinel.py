"""
core/observability/sentinel.py
Autonomous self-healing service for Neurex. Monitors port health and auto-restarts 
failed background services.
"""
from __future__ import annotations

import asyncio
import os
import socket
from pathlib import Path

import structlog

log = structlog.get_logger()

SERVICES = {
    "api":    {"port": 8000, "type": "api"},
    "web":    {"port": 3000, "type": "web"},
    "ollama": {"port": 11434, "type": "engine", "name": "ollama"},
}

class Sentinel:
    def __init__(self, check_interval: int = 30):
        self.check_interval = check_interval
        self._running = False
        # Phase 55: Robust Workspace Detection
        env_ws = os.getenv("WORKSPACE_PATH")
        if env_ws:
            self.workspace = Path(env_ws)
        else:
            # Fallback: Detect from file location
            self.workspace = Path(__file__).parent.parent.parent.parent
        
        log.info("sentinel.init", workspace=str(self.workspace))

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
                    await self._restart_service(name, config)
                else:
                    log.debug("sentinel.service_ok", service=name, port=port)
            
            await asyncio.sleep(self.check_interval)

    def _is_port_open(self, port: int) -> bool:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.settimeout(1)
            try:
                s.connect(("127.0.0.1", port))
                return True
            except (TimeoutError, ConnectionRefusedError):
                return False

    async def _restart_service(self, name: str, config: dict):
        log.info("sentinel.attempting_restart", service=name)
        
        try:
            if config["type"] == "engine":
                from core.infrastructure.manager import infrastructure_manager
                await infrastructure_manager.start_engine(config["name"])
            elif config["type"] == "api":
                # API restart is tricky since we ARE the API. 
                # But we can try to run the Makefile target if we're in a separate process
                # Or just log it for now as a critical failure.
                log.error("sentinel.api_down_self_check_failed", hint="Manual restart required or use external supervisor")
            elif config["type"] == "web":
                import subprocess
                subprocess.Popen(
                    ["make", "dev-web"],
                    cwd=self.workspace,
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                    start_new_session=True
                )
            
            log.info("sentinel.restart_initiated", service=name)
        except Exception as e:
            log.error("sentinel.restart_failed", service=name, error=str(e))

sentinel = Sentinel()

