"""
core/context/scratchpad.py
Persistent shared scratchpad for inter-agent communication during graph execution.
"""

import json
import os
from pathlib import Path

import structlog

log = structlog.get_logger()

# Scratchpads are stored per-conversation
SCRATCHPAD_DIR = Path(os.getenv("WORKSPACE_PATH", "/workspace")) / ".neurex" / "scratchpads"


async def set_scratchpad_value(conversation_id: str, key: str, value: str) -> str:
    """Store a persistent note or variable for the current conversation."""
    # SECURITY: Sanitize conversation_id to prevent path traversal
    import re

    if not re.match(r"^[a-zA-Z0-9_\-]+$", conversation_id):
        raise ValueError("Invalid conversation_id")

    SCRATCHPAD_DIR.mkdir(parents=True, exist_ok=True)

    safe_dir = os.path.realpath(str(SCRATCHPAD_DIR))
    file_path_str = os.path.realpath(os.path.join(safe_dir, f"{conversation_id}.json"))
    safe_prefix = safe_dir if safe_dir.endswith(os.sep) else safe_dir + os.sep
    if not file_path_str.startswith(safe_prefix):
        raise ValueError("Security violation: Path traversal attempted")

    file_path = Path(file_path_str)

    data = {}
    if file_path.exists():
        with open(file_path) as f:
            data = json.load(f)

    data[key] = value

    with open(file_path, "w") as f:
        json.dump(data, f, indent=2)

    log.info("scratchpad.set", conversation_id=conversation_id, key=key)
    return f"✅ Scratchpad updated: {key} set."


async def get_scratchpad(conversation_id: str) -> dict:
    """Retrieve all shared notes for the current conversation."""
    # SECURITY: Sanitize conversation_id
    import re

    if not re.match(r"^[a-zA-Z0-9_\-]+$", conversation_id):
        return {}

    safe_dir = os.path.realpath(str(SCRATCHPAD_DIR))
    file_path_str = os.path.realpath(os.path.join(safe_dir, f"{conversation_id}.json"))
    safe_prefix = safe_dir if safe_dir.endswith(os.sep) else safe_dir + os.sep
    if not file_path_str.startswith(safe_prefix):
        return {}

    file_path = Path(file_path_str)
    if not file_path.exists():
        return {}

    with open(file_path) as f:
        return json.load(f)


async def clear_scratchpad(conversation_id: str) -> str:
    """Clear all shared notes for the current conversation."""
    # SECURITY: Sanitize conversation_id
    import re

    if not re.match(r"^[a-zA-Z0-9_\-]+$", conversation_id):
        return "❌ Invalid ID."

    safe_dir = os.path.realpath(str(SCRATCHPAD_DIR))
    file_path_str = os.path.realpath(os.path.join(safe_dir, f"{conversation_id}.json"))
    safe_prefix = safe_dir if safe_dir.endswith(os.sep) else safe_dir + os.sep
    if not file_path_str.startswith(safe_prefix):
        return "❌ Security violation."

    file_path = Path(file_path_str)
    if file_path.exists():
        file_path.unlink()
    return "✅ Scratchpad cleared."
