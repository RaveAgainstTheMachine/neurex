import json
import logging
import os
from pathlib import Path

import structlog

# Use the absolute path to the project root for logs
# Dynamically determine base directory
BASE_DIR = Path(os.getenv("WORKSPACE_PATH", os.getcwd())).parent
LOG_FILE = BASE_DIR / ".neurex" / "audit.jsonl"
log = structlog.get_logger()


def setup_logging():
    LOG_FILE.parent.mkdir(parents=True, exist_ok=True)

    processors = [
        structlog.processors.add_log_level,
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.JSONRenderer(),
    ]

    # Configure structlog to append to our audit file
    structlog.configure(
        processors=processors,
        logger_factory=structlog.WriteLoggerFactory(
            file=open(LOG_FILE, "a", buffering=1)  # Line buffered
        ),
    )


def get_audit_logs(limit=100):
    if not LOG_FILE.exists():
        return []

    logs = []
    try:
        with open(LOG_FILE) as f:
            lines = f.readlines()
            for line in lines[-limit:]:
                if not line.strip():
                    continue
                try:
                    log_data = json.loads(line)
                    logs.append(
                        {
                            "id": str(hash(line)),
                            "timestamp": log_data.get("timestamp"),
                            "level": log_data.get("level", "INFO").upper(),
                            "event": log_data.get("event", "unknown"),
                            "user_id": log_data.get("user_id", "system"),
                            "ip_address": log_data.get("ip_address", "internal"),
                            "details": json.dumps(log_data, indent=2),
                        }
                    )
                except Exception:
                    continue
    except Exception as e:
        logging.error(f"Error reading logs: {e}")

    return logs[::-1]
