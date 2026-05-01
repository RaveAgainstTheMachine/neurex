"""
core/harness/kairos.py
The "Kairos" Background Daemon (autoDream).
Continuously monitors the repository and updates architectural intelligence.
Inspired by the 'KAIROS' feature revealed in the Claude Code leak.
"""
from __future__ import annotations
import asyncio
import os
import time
import structlog
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
from core.mcp.tools.intel import synthesize_project_intel

log = structlog.get_logger()

class KairosHandler(FileSystemEventHandler):
    def __init__(self, loop, workspace_path):
        self.loop = loop
        self.ws = workspace_path
        self.last_run = 0
        self.cooldown = 30 # Seconds between summarizations

    def on_modified(self, event):
        if event.is_directory:
            return
        if ".git" in event.src_path or ".neurex" in event.src_path:
            return
            
        current_time = time.time()
        if current_time - self.last_run > self.cooldown:
            log.info("kairos.change_detected", path=event.src_path)
            self.last_run = current_time
            # Schedule the dream loop
            asyncio.run_coroutine_threadsafe(self.dream(), self.loop)

    async def dream(self):
        """The 'autoDream' loop: synthesizes changes into persistent memory."""
        log.info("kairos.auto_dream_start")
        try:
            # 1. Update project intel (AST-aware)
            await synthesize_project_intel()
            
            # 2. Update MEMORY.md (Skeptical Memory)
            from core.context.skeptical_memory import SkepticalMemory
            memory = SkepticalMemory(self.ws)
            # Lightweight summarization (Caveman style)
            summary = f"Kairos autoDream completed at {time.ctime()}. Codebase structure synchronized."
            memory.update_memory(summary)
            
            log.info("kairos.auto_dream_complete")
        except Exception as e:
            log.error("kairos.dream_failed", error=str(e))

class KairosDaemon:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(KairosDaemon, cls).__new__(cls)
            cls._instance.observer = None
            cls._instance.is_running = False
        return cls._instance

    def start(self, workspace_path: str):
        if self.is_running:
            return
        
        log.info("kairos.daemon_starting", path=workspace_path)
        loop = asyncio.get_event_loop()
        handler = KairosHandler(loop, workspace_path)
        self.observer = Observer()
        self.observer.schedule(handler, workspace_path, recursive=True)
        self.observer.start()
        self.is_running = True

    def stop(self):
        if not self.is_running:
            return
        log.info("kairos.daemon_stopping")
        self.observer.stop()
        self.observer.join()
        self.is_running = False

kairos_daemon = KairosDaemon()
