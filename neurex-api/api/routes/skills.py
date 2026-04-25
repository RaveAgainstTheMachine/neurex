"""
api/routes/skills.py
Endpoints for managing external Neurex skills.
"""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from core.skills.manager import SkillManager, SKILLS_DIR

router = APIRouter()
manager = SkillManager()

class SkillInstallRequest(BaseModel):
    url: str

@router.get("/")
async def list_skills():
    """List all installed skills and their tools."""
    skills = []
    for skill_dir in SKILLS_DIR.iterdir():
        if skill_dir.is_dir() and not skill_dir.name.startswith("."):
            from core.skills.manager import SkillSet
            s = SkillSet(skill_dir.name, skill_dir)
            skills.append({
                "id": s.name,
                "name": s.manifest.get("display_name", s.name),
                "description": s.manifest.get("description", ""),
                "tools_count": len(s.tools),
                "url": s.manifest.get("repository", "")
            })
    return skills

@router.post("/install")
async def install_skill(req: SkillInstallRequest):
    """Clone a new skill from Git."""
    try:
        name = manager.install_from_git(req.url)
        return {"status": "success", "skill": name}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/{skill_id}")
async def uninstall_skill(skill_id: str):
    """Remove a skill from the system."""
    target = SKILLS_DIR / skill_id
    if target.exists() and target.is_dir():
        import shutil
        shutil.rmtree(target)
        return {"status": "deleted"}
    raise HTTPException(status_code=404, detail="Skill not found")
