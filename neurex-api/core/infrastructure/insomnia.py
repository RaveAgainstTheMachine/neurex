"""
core/infrastructure/insomnia.py
Prevents system sleep when enabled.
"""

import structlog

import wakelock
from core.settings.manager import settings_manager

log = structlog.get_logger()


class InsomniaService:
    def __init__(self):
        self.is_active = False

    def sync(self):
        """Update system sleep state based on current settings."""
        should_be_awake = settings_manager.get("enable_insomnia")

        if should_be_awake and not self.is_active:
            try:
                wakelock.lock()
                self.is_active = True
                log.info("system.insomnia_active", status="locked")
            except Exception as e:
                log.error("system.insomnia_failed", error=str(e))

        elif not should_be_awake and self.is_active:
            try:
                wakelock.unlock()
                self.is_active = False
                log.info("system.insomnia_inactive", status="released")
            except Exception as e:
                log.error("system.insomnia_unlock_failed", error=str(e))


insomnia_service = InsomniaService()
