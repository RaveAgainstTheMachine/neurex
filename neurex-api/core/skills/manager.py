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

    def list_available(self) -> List[Dict[str, Any]]:
        """Scan skills directory and return metadata for all installed skills."""
        skills = []
        if not SKILLS_DIR.exists():
            return []
        for d in SKILLS_DIR.iterdir():
            if d.is_dir() and not d.name.startswith("."):
                manifest_path = d / "manifest.json"
                m = {}
                if manifest_path.exists():
                    with open(manifest_path, "r") as f:
                        m = json.load(f)
                
                skills.append({
                    "id": d.name,
                    "name": m.get("name", d.name),
                    "description": m.get("description", "No description available."),
                    "version": m.get("version", "0.1.0"),
                    "author": m.get("author", "unknown"),
                    "enabled": True, # Placeholder for state management
                    "source_repo": m.get("repository", "")
                })
        return skills

    def get_enabled_tools(self) -> List[Dict[str, Any]]:
        """Scan skills directory and return all tool definitions."""
        all_tools = []
        self._tool_to_skill = {} # Map tool_name -> skill_name for dispatch
        
        if not SKILLS_DIR.exists():
            return []

        for skill_dir in SKILLS_DIR.iterdir():
            if skill_dir.is_dir() and not skill_dir.name.startswith("."):
                try:
                    skill = SkillSet(skill_dir.name, skill_dir)
                    for tool in skill.tools:
                        tool_name = tool.get("function", {}).get("name")
                        if tool_name:
                            self._tool_to_skill[tool_name] = skill_dir.name
                    all_tools.extend(skill.tools)
                except Exception as e:
                    log.warning("skill.load_failed", name=skill_dir.name, error=str(e))
        return all_tools

    def get_skill_for_tool(self, tool_name: str) -> str | None:
        """Return the skill name that provides the given tool."""
        # Ensure we've scanned
        if not hasattr(self, "_tool_to_skill"):
            self.get_enabled_tools()
        return self._tool_to_skill.get(tool_name)

    def fetch_curated_list(self) -> List[Dict[str, Any]]:
        """Fetch the curated list from the Neurex Skills Marketplace."""
        import requests
        try:
            url = "https://skills.mp/api/v1/registry.json"
            resp = requests.get(url, timeout=5)
            if resp.status_code == 200:
                return resp.json().get("skills", [])
        except Exception as e:
            log.warning("skill.fetch_curated_failed", error=str(e))
        return []

    def delete_skill(self, name: str) -> bool:
        """Remove a skill from the local store."""
        target_path = SKILLS_DIR / name
        if target_path.exists() and target_path.is_dir():
            log.info("skill.delete", name=name)
            shutil.rmtree(target_path)
            return True
        return False

    async def execute_skill_tool(self, skill_name: str, tool_name: str, args: Dict[str, Any]) -> str:
        skill_path = SKILLS_DIR / skill_name
        handler_path = skill_path / "handler.py"
        if not handler_path.exists():
            return f"Error: Skill '{skill_name}' does not have a handler.py"
        import importlib.util
        import sys
        try:
            module_name = f"neurex_skill_{skill_name}"
            spec = importlib.util.spec_from_file_location(module_name, str(handler_path))
            if not spec or not spec.loader:
                return f"Error: Could not load handler for skill '{skill_name}'"
            module = importlib.util.module_from_spec(spec)
            sys.modules[module_name] = module
            spec.loader.exec_module(module)
            if not hasattr(module, "handle"):
                return f"Error: Skill '{skill_name}' handler has no 'handle' function"
            result = await module.handle(tool_name, args)
            return str(result)
        except Exception as e:
            log.error("skill.execution_failed", skill=skill_name, tool=tool_name, error=str(e))
            return f"Skill execution error: {str(e)}"
