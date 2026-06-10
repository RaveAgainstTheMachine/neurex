"""
core/harness/somnus.py
The "Somnus" Background Daemon (autoDream).
Continuously monitors the repository and updates architectural intelligence.
Replaces the 'Kairos' protocol with a native Neurex persistent observer.
"""

from __future__ import annotations

import time

import structlog

from core.mcp.tools.intel import synthesize_project_intel

log = structlog.get_logger()


class SomnusDaemon:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance.is_running = False
            cls._instance.last_run = 0
            cls._instance.cooldown = 30
            cls._instance.ws = None
        return cls._instance

    def start(self, workspace_path: str):
        # Called from main.py lifespan to signal it's ready and set the workspace
        if self.is_running:
            return
        log.info("somnus.daemon_starting", path=workspace_path)
        self.ws = workspace_path
        self.is_running = True

    def stop(self):
        if not self.is_running:
            return
        log.info("somnus.daemon_stopping")
        self.is_running = False

    async def on_change(self, paths: list[str]):
        if not self.is_running:
            return

        # Check if change is relevant
        relevant = False
        for path in paths:
            if ".git" not in path and ".neurex" not in path:
                relevant = True
                break
        
        if not relevant:
            return

        current_time = time.time()
        if current_time - self.last_run > self.cooldown:
            log.info("somnus.change_detected", count=len(paths))
            self.last_run = current_time
            await self.dream()

    async def dream(self):
        """The 'autoDream' loop: synthesizes changes and harvests mesh skills."""
        from core.settings.manager import settings_manager
        
        read_autonomy = settings_manager.get("background_read_autonomy_level")
        write_autonomy = settings_manager.get("background_write_autonomy_level")
        log.info("somnus.auto_dream_start", read_autonomy=read_autonomy, write_autonomy=write_autonomy)
        
        try:
            # 1. Update project intel (AST-aware)
            await synthesize_project_intel()

            # 2. Update MEMORY.md (Skeptical Memory)
            from core.context.skeptical_memory import SkepticalMemory

            memory = SkepticalMemory(self.ws)
            summary = (
                f"Somnus autoDream completed at {time.ctime()}. Codebase structure synchronized."
            )
            memory.update_memory(summary)

            # 3. Harvest Mesh Skills (Phase 35)
            from core.skills.harvester import harvester

            await harvester.harvest_from_mesh()

            log.info("somnus.auto_dream_complete")
        except Exception as e:
            log.error("somnus.dream_failed", error=str(e))

somnus_daemon = SomnusDaemon()
