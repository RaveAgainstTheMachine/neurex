"""
core/context/rules_parser.py
Loads and merges .neurexrules files.
Robust parser that supports [section] headers without INI strictness.
"""
from __future__ import annotations

import os
import re
from pathlib import Path

import structlog

log = structlog.get_logger()

# Workspace path from environment (loaded via dotenv in main.py)
WORKSPACE_PATH = Path(os.getenv("WORKSPACE_PATH", "/workspace"))
GLOBAL_RULES   = Path.home() / ".neurexrules"
PROJECT_RULES  = WORKSPACE_PATH / ".neurexrules"

class RulesParser:
    def __init__(self):
        self._rules: dict[str, list[str]] = {
            "always":  [],
            "coder":   [],
            "tester":  [],
            "planner": [],
            "researcher": [],
            "reviewer":   [],
        }
        self._load()

    def _load(self):
        sources = [GLOBAL_RULES, PROJECT_RULES]
        for path in sources:
            if path.exists():
                self._parse_file(path)
                log.info("rules_parser.loaded", path=str(path))
            else:
                log.debug("rules_parser.not_found", path=str(path))

    def _parse_file(self, path: Path):
        """
        Simple manual parser that handles [section] headers.
        Treats every non-empty line as a rule.
        """
        current_section = "always"
        raw = path.read_text(errors="replace")
        
        for line in raw.splitlines():
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            
            # Check for section header: [section]
            match = re.match(r"^\[(\w+)\]$", line)
            if match:
                current_section = match.group(1).lower()
                if current_section not in self._rules:
                    self._rules[current_section] = []
                continue
            
            # Add line to current section
            if current_section in self._rules:
                self._rules[current_section].append(line)
            else:
                self._rules["always"].append(line)

    def get_merged_rules(self, agent_type: str | None = None) -> str:
        """Returns merged rules for injection into system prompt."""
        # Always start with 'always' rules
        rules_set = set(self._rules["always"])
        
        # Add agent-specific rules
        if agent_type and agent_type in self._rules:
            rules_set.update(self._rules[agent_type])
            
        if not rules_set:
            return ""
            
        # Return as sorted list for determinism
        lines = sorted(list(rules_set))
        return "\n".join(f"- {line}" for line in lines)

    def reload(self):
        for key in self._rules:
            self._rules[key] = []
        self._load()
        log.info("rules_parser.reloaded")
