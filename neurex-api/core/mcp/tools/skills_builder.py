"""
core/mcp/tools/skills_builder.py
Tools for autonomous skill authorship and expansion.
"""
import os
import json
import shutil
import structlog
from pathlib import Path

log = structlog.get_logger()

# Dynamically determine skills directory
os.environ["WORKSPACE_PATH"] = os.getenv("WORKSPACE_PATH", os.getcwd())
ws = os.getenv("WORKSPACE_PATH")
SKILLS_DIR = os.getenv("SKILLS_DIR", os.path.join(ws, "neurex-api", "skills"))

async def create_skill(name: str, description: str, logic_code: str) -> str:
    """
    Generate a new Neurex skill.
    - Creates the skill directory
    - Writes metadata.json
    - Writes the main skill logic (Python)
    """
    skill_path = Path(SKILLS_DIR) / name
    if skill_path.exists():
        return f"Error: Skill '{name}' already exists."
        
    try:
        skill_path.mkdir(parents=True)
        
        # 1. Manifest (SkillManager expects manifest.json)
        manifest = {
            "name": name,
            "description": description,
            "version": "0.1.0",
            "tools": [
                {
                    "function": {
                        "name": f"{name}_tool",
                        "description": f"Main tool for {name}",
                        "parameters": {
                            "type": "object",
                            "properties": {
                                "input": {"type": "string"}
                            }
                        }
                    }
                }
            ]
        }
        with open(skill_path / "manifest.json", "w") as f:
            json.dump(manifest, f, indent=2)
            
        # 2. Handler (SkillManager expects handler.py with a handle() function)
        handler_template = f"""\
\"\"\"
Autonomous Handler for {name}
\"\"\"
async def handle(tool_name: str, args: dict):
    # Agent-provided logic:
{logic_code}
"""
        with open(skill_path / "handler.py", "w") as f:
            f.write(handler_template)
            
        return f"✅ Skill '{name}' created. Run 'publish_skill' to enable."
    except Exception as e:
        log.error("skills_builder.create_failed", skill=name, error=str(e))
        ws = os.getenv("WORKSPACE_PATH", "/workspace")
        path = os.path.join(ws, "artifacts", str(name))
        return f"Error: Failed to create skill: {e}"

async def publish_skill(name: str) -> str:
    """
    Register and enable a locally created skill.
    """
    skill_path = Path(SKILLS_DIR) / name
    if not skill_path.exists():
        return f"Error: Skill '{name}' not found."
        
    try:
        # In a real implementation, this would trigger the SkillManager to reload.
        # Since we are in the same process, we can just log success and the 
        # SkillManager will pick it up on the next tool scan.
        log.info("skills_builder.published", skill=name)
        return f"🚀 Skill '{name}' published. Agents can now use tools from this skill."
    except Exception as e:
        return f"Error: Failed to publish skill: {e}"
