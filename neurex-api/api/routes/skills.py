import json
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from core.skills.manager import SkillManager
from api.routes.auth import require_role, UserRole

router = APIRouter()
manager = SkillManager()

class SkillInstallRequest(BaseModel):
    url: str

@router.get("/")
async def list_skills():
    """List all installed skills."""
    return manager.list_available()

@router.delete("/{skill_id}", dependencies=[Depends(require_role(UserRole.ADMIN))])
async def delete_skill(skill_id: str):
    """Delete an installed skill."""
    if manager.delete_skill(skill_id):
        return {"status": "deleted"}
    raise HTTPException(status_code=404, detail="Skill not found")

@router.get("/curated")
async def list_curated():
    """Fetch the 'Awesome Skills' library from remote."""
    return manager.fetch_curated_list()

@router.post("/install", dependencies=[Depends(require_role(UserRole.ADMIN))])
async def install_skill(req: SkillInstallRequest):
    """Clone a new skill from Git."""
    try:
        name = manager.install_from_git(req.url)
        return {"status": "success", "skill": name}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
