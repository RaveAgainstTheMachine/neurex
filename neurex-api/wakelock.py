"""
wakelock module for Neurex.
Prevents system sleep during long-running background tasks.
"""

import structlog

log = structlog.get_logger()
_mode = None


def lock():
    """Acquire system sleep prevention lock using wakepy."""
    global _mode
    try:
        from wakepy import keep
        # Acquire keep.running() to prevent system sleep while keeping screen behavior default
        _mode = keep.running()
        _mode.__enter__()
        log.info("wakelock.acquired", message="System sleep prevention active (wakepy.keep.running)")
    except ImportError:
        log.warning("wakelock.unsupported", message="wakepy not installed. Sleep prevention operates as no-op.")
    except Exception as e:
        log.warning("wakelock.failed", error=str(e), message="Failed to acquire system power assertions. Proceeding without sleep prevention.")


def unlock():
    """Release system sleep prevention lock."""
    global _mode
    if _mode:
        try:
            _mode.__exit__(None, None, None)
            _mode = None
            log.info("wakelock.released", message="System sleep prevention released cleanly")
        except Exception as e:
            log.error("wakelock.release_failed", error=str(e))

