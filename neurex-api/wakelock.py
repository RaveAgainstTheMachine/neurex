"""
Mock wakelock module for Neurex.
Used when the real wakelock package cannot be installed.
"""
import structlog

log = structlog.get_logger()

def lock():
    log.info("wakelock.mock_lock", message="System sleep prevention mocked (No-op)")

def unlock():
    log.info("wakelock.mock_unlock", message="System sleep prevention released (No-op)")
