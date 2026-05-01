"""
core/context/skeptical_memory.py
Implements "Skeptical Memory Management" inspired by state-of-the-art agentic harnesses.
Forces agents to verify state via grep/read before acting and maintains a
lightweight sticky-note memory for high-speed context restoration.
"""
from __future__ import annotations
import os
import structlog
from typing import List, Dict

log = structlog.get_logger()

class SkepticalMemory:
    def __init__(self, workspace_path: str):
        self.ws = workspace_path
        self.memory_file = os.path.join(workspace_path, ".neurex", "MEMORY.md")
        os.makedirs(os.path.dirname(self.memory_file), exist_ok=True)

    def update_memory(self, sticky_note: str):
        """Updates the high-speed pointer file."""
        try:
            with open(self.memory_file, "w") as f:
                f.write(f"## NEUREX AGENT MEMORY\nLast Update: {os.popen('date').read()}\n\n{sticky_note}")
            log.info("memory.updated", path=self.memory_file)
        except Exception as e:
            log.error("memory.update_failed", error=str(e))

    def get_memory(self) -> str:
        """Retrieves the current sticky note context."""
        if not os.path.exists(self.memory_file):
            return ""
        try:
            with open(self.memory_file, "r") as f:
                return f.read()
        except:
            return ""

    def get_skeptical_instruction(self) -> str:
        """Returns the prompt directive for skeptical execution."""
        return """
        SKEPTICAL EXECUTION ENABLED:
        - Never trust your internal memory regarding file contents.
        - ALWAYS verify file state using 'grep' or 'read_file' before attempting a 'write_file'.
        - If a file has changed since your last read, re-read it before acting.
        - Document your current progress in the .neurex/MEMORY.md sticky note after every major step.
        """

# Integrated into BaseAgent and Orchestrator
