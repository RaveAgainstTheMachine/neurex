# neurex-api/core/infrastructure/watcher.py
import asyncio
import os
from pathlib import Path
import structlog
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
from core.collaboration.presence import presence_manager

log = structlog.get_logger()

class WatcherHandler(FileSystemEventHandler):
    def __init__(self, loop: asyncio.AbstractEventLoop):
        self.loop = loop
        self._last_event = 0

    def _broadcast(self):
        # Debounce broadcast
        import time
        now = time.time()
        if now - self._last_event < 1.5:
            return
        self._last_event = now
        
        asyncio.run_coroutine_threadsafe(
            presence_manager.broadcast_global({
                "event": "file_system_changed",
                "data": {}
            }),
            self.loop
        )

    def _should_ignore(self, path: str) -> bool:
        ignored_parts = {".git", "node_modules", "venv", ".venv", "__pycache__", ".neurex"}
        parts = set(Path(path).parts)
        if parts.intersection(ignored_parts):
            return True
        if path.endswith(".log"):
            return True
        return False

    def on_modified(self, event):
        if not event.is_directory and not self._should_ignore(event.src_path):
            self._broadcast()

    def on_created(self, event):
        if not self._should_ignore(event.src_path):
            self._broadcast()

    def on_deleted(self, event):
        if not self._should_ignore(event.src_path):
            self._broadcast()

    def on_moved(self, event):
        if not self._should_ignore(event.src_path) and not self._should_ignore(event.dest_path):
            self._broadcast()

class WatcherService:
    def __init__(self):
        self.observer = None

    def start(self):
        try:
            from api.routes.files import get_workspace
            workspace_path = get_workspace()
            loop = asyncio.get_running_loop()
            handler = WatcherHandler(loop)
            self.observer = Observer()
            self.observer.schedule(handler, str(workspace_path), recursive=True)
            self.observer.start()
            log.info("watcher.started", path=str(workspace_path))
        except Exception as e:
            log.error("watcher.failed", error=str(e))

    def stop(self):
        if self.observer:
            self.observer.stop()
            self.observer.join()
            log.info("watcher.stopped")

watcher_service = WatcherService()
