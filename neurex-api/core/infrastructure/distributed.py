"""
core/infrastructure/distributed.py
Manages llama.cpp RPC server lifecycle for distributed tensor pooling.
"""
import asyncio
import structlog
import subprocess
import os
from typing import Optional
from core.settings.manager import settings_manager

log = structlog.get_logger()

class DistributedManager:
    def __init__(self):
        self.rpc_process: Optional[subprocess.Popen] = None
        self.port = 50051 # Default llama.cpp RPC port

    async def start_rpc_server(self):
        """Starts the llama-rpc-server to allow this node to act as a compute worker."""
        if self.rpc_process:
            return

        if not settings_manager.get("enable_distributed_pooling"):
            return

        # Path to llama-rpc-server (assumed to be in PATH or configured)
        cmd = ["llama-rpc-server", "--port", str(self.port)]
        
        try:
            log.info("mesh.rpc_server_starting", port=self.port)
            self.rpc_process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
            log.info("mesh.rpc_server_active", pid=self.rpc_process.pid)
        except Exception as e:
            log.error("mesh.rpc_server_failed", error=str(e))

    def stop_rpc_server(self):
        """Terminates the worker process."""
        if self.rpc_process:
            self.rpc_process.terminate()
            self.rpc_process = None
            log.info("mesh.rpc_server_stopped")

    def get_rpc_address(self) -> str:
        """Returns the local IP and port for master discovery."""
        # In a real mesh, we'd use the mesh-defined IP
        return f"0.0.0.0:{self.port}"

distributed_manager = DistributedManager()
