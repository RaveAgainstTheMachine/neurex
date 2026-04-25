"""
core/skills/manager.py
Dynamic plugin loader for community skills and MCP tool expansions.
"""
import os
import importlib.util
from pathlib import Path
from pydantic import BaseModel
from typing import List, Dict, Any
import structlog

log = structlog.get_logger()

SKILLS_DIR = Path(os.getenv("SKILLS_PATH", "/workspace/.neurex/skills"))

class SkillManifest(BaseModel):
    id: str
    name: str
    description: str
    version: str
    author: str
    enabled: bool
    source_repo: str = ""

# Pre-baked community skills index
COMMUNITY_SKILLS = [
    SkillManifest(
        id="awesome-skills",
        name="Antigravity Awesome Skills",
        description="A curated collection of highly effective agentic tools for data scraping, system monitoring, and advanced reasoning.",
        version="1.0.0",
        author="sickn33",
        enabled=False,
        source_repo="https://github.com/sickn33/antigravity-awesome-skills"
    ),
    SkillManifest(
        id="caveman",
        name="Caveman Base Tools",
        description="Primitive but extremely robust shell operations and raw text manipulation tools that never fail.",
        version="0.9.1",
        author="community",
        enabled=False,
        source_repo="https://github.com/community/caveman"
    )
]

class SkillManager:
    def __init__(self):
        self.active_skills = {}
        SKILLS_DIR.mkdir(parents=True, exist_ok=True)

    def list_available(self) -> List[SkillManifest]:
        """Return the index of pre-baked and installed skills."""
        return COMMUNITY_SKILLS
        
    def toggle_skill(self, skill_id: str, enable: bool) -> bool:
        """Enable or disable a specific skill."""
        for skill in COMMUNITY_SKILLS:
            if skill.id == skill_id:
                skill.enabled = enable
                log.info("skill.toggled", skill=skill_id, enabled=enable)
                return True
        return False

    def load_local_skills(self):
        """Dynamically import .py files in SKILLS_DIR as MCP extensions."""
        for file in SKILLS_DIR.glob("*.py"):
            if file.stem == "__init__": continue
            try:
                spec = importlib.util.spec_from_file_location(file.stem, file)
                module = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(module)
                
                # Check if module exposes an MCP register function
                if hasattr(module, "register_tools"):
                    module.register_tools()
                    self.active_skills[file.stem] = module
                    log.info("skill.loaded", name=file.stem)
            except Exception as e:
                log.error("skill.load_failed", name=file.stem, error=str(e))
