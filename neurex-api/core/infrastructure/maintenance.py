"""
core/infrastructure/maintenance.py
Phase 45: Sentient IDE (Predictive Maintenance)
Monitors telemetry and filesystem churn to proactively trigger workspace re-indexing.
Ensures that the Mesh intelligence (RAG/Memory) remains synchronized with the physical state of the codebase.
"""

import asyncio
from datetime import UTC, datetime

import structlog

log = structlog.get_logger()


class PredictiveMaintenance:
    def __init__(self):
        self.churn_buffer: set[str] = set()
        self.last_index_time = datetime.now(UTC)
        self.churn_threshold = 50  # Trigger re-index after 50 distinct file changes
        self.index_interval = 3600  # Force re-index every hour regardless of churn
        self._lock = asyncio.Lock()
        self._indexing_active = False

    async def report_churn(self, paths: list[str]):
        """
        Adds paths to the churn buffer and evaluates if a proactive re-index is required.
        Called by the WatcherService.
        """
        async with self._lock:
            for p in paths:
                self.churn_buffer.add(p)

            log.debug("maintenance.churn_tracked", current_churn=len(self.churn_buffer))

            if len(self.churn_buffer) >= self.churn_threshold:
                log.info(
                    "maintenance.proactive_index_triggered",
                    reason="high_churn",
                    count=len(self.churn_buffer),
                )
                asyncio.create_task(self.trigger_maintenance_task())

    async def start_background_monitor(self):
        """Periodically checks for stale indices."""
        while True:
            await asyncio.sleep(300)  # Check every 5 minutes
            now = datetime.now(UTC)
            delta = (now - self.last_index_time).total_seconds()

            if delta >= self.index_interval:
                log.info("maintenance.proactive_index_triggered", reason="stale_index")
                asyncio.create_task(self.trigger_maintenance_task())

    async def trigger_maintenance_task(self):
        """
        Executes a background re-indexing of the workspace.
        Delegates to MemoryWorker._full_index() which uses a 10-semaphore parallel
        pipeline over the entire WORKSPACE_PATH. Gracefully no-ops when ChromaDB
        is unavailable (memory_worker._enabled == False).
        """
        if self._indexing_active:
            return

        async with self._lock:
            self._indexing_active = True

        try:
            log.info("maintenance.indexing_started")

            # Reset churn before indexing so new changes accumulated during the run
            # are tracked in the next cycle rather than silently dropped.
            self.churn_buffer.clear()
            self.last_index_time = datetime.now(UTC)

            from core.memory.worker import memory_worker

            if memory_worker._enabled:
                await memory_worker._full_index()
                log.info("maintenance.indexing_complete")
            else:
                log.info("maintenance.indexing_skipped", reason="memory_worker_disabled")
        finally:
            async with self._lock:
                self._indexing_active = False


maintenance_service = PredictiveMaintenance()
