"""
core/skills/manager.py
Manages external skill sets (MCP tool collections).
Supports downloading, validating, and dynamic registration.
"""
from __future__ import annotations
import os
import json
import shutil
import subprocess
from pathlib import Path
from typing import List, Dict, Any
import structlog

log = structlog.get_logger()

SKILLS_DIR = Path(os.getenv("WORKSPACE_PATH", "/workspace")) / ".neurex" / "skills"

class SkillSet:
    def __init__(self, name: str, path: Path):
        self.name = name
        self.path = path
        self.manifest = self._load_manifest()

    def _load_manifest(self) -> Dict[str, Any]:
        manifest_path = self.path / "manifest.json"
        if manifest_path.exists():
            with open(manifest_path, "r") as f:
                return json.load(f)
        return {}

    @property
    def tools(self) -> List[Dict[str, Any]]:
        return self.manifest.get("tools", [])

class SkillManager:
    def __init__(self):
        SKILLS_DIR.mkdir(parents=True, exist_ok=True)

    def install_from_git(self, url: str) -> str:
        """Clone a skill repository into the local skills store."""
        name = url.split("/")[-1].replace(".git", "")
        target_path = SKILLS_DIR / name
        
        if target_path.exists():
            log.info("skill.update", name=name)
            subprocess.run(["git", "pull"], cwd=target_path, check=True)
        else:
            log.info("skill.install", name=name, url=url)
            subprocess.run(["git", "clone", url, str(target_path)], check=True)
        
        return name

    def get_enabled_tools(self) -> List[Dict[str, Any]]:
        """Scan skills directory and return all tool definitions."""
        all_tools = []
        for skill_dir in SKILLS_DIR.iterdir():
            if skill_dir.is_dir() and not skill_dir.name.startswith("."):
                skill = SkillSet(skill_dir.name, skill_dir)
                all_tools.extend(skill.tools)
        return all_tools

    def fetch_curated_list(self) -> List[Dict[str, Any]]:
        """Fetch the curated 'Awesome Skills' manifest from GitHub."""
        import requests
        try:
            # We point to the raw manifest.json in the awesome-skills repo
            url = "https://raw.githubusercontent.com/sickn33/antigravity-awesome-skills/main/skills.json"
            resp = requests.get(url, timeout=5)
            if resp.status_code == 200:
                return resp.json().get("skills", [])
        except Exception as e:
            log.warning("skill.fetch_curated_failed", error=str(e))
        return []

    def execute_skill_tool(self, skill_name: str, tool_name: str, args: Dict[str, Any]) -> str:
        """
        Execute a tool provided by a specific skill.
        Skills are expected to provide a 'handler.py' or equivalent entry point.
        """
        # TODO: Implement dynamic execution of skill-specific logic
        return f"Skill tool '{tool_name}' execution not yet implemented for '{skill_name}'"
