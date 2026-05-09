from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field

from api.routes.auth import UserRole, require_role
from core.skills.manager import SkillManager

router = APIRouter()
manager = SkillManager()

class SkillInstallRequest(BaseModel):
    url: str = Field(..., description="The Git repository URL or subpath URL")

@router.get("/")
async def list_skills():
    """List all installed skills."""
    return manager.list_available()

@router.get("/curated")
async def list_curated():
    """Fetch the 'Awesome Skills' library from remote."""
    return manager.fetch_curated_list()

@router.get("/{skill_id}", dependencies=[Depends(require_role(UserRole.DEVELOPER))])
async def get_skill_details(skill_id: str):
    """Get full details for a skill. Validates ID to prevent traversal."""
    if not skill_id.isalnum() and "-" not in skill_id and "_" not in skill_id:
        raise HTTPException(status_code=400, detail="Invalid skill ID format")
        
    details = manager.get_skill_details(skill_id)
    if not details:
        raise HTTPException(status_code=404, detail="Skill not found")
    return details

@router.delete("/{skill_id}", dependencies=[Depends(require_role(UserRole.ADMIN))])
async def delete_skill(skill_id: str):
    """Delete an installed skill."""
    if manager.delete_skill(skill_id):
        return {"status": "deleted"}
    raise HTTPException(status_code=404, detail="Skill not found")

@router.post("/install", dependencies=[Depends(require_role(UserRole.ADMIN))])
async def install_skill(req: SkillInstallRequest):
    """Clone a new skill from Git."""
    try:
        name = manager.install_from_git(req.url)
        return {"status": "success", "skill": name}
    except ValueError as ve:
        raise HTTPException(status_code=400, detail=str(ve))
    except Exception as e:
        # Don't leak full tracebacks, but provide the core error
        err_msg = str(e)
        if "already exists" in err_msg:
            raise HTTPException(status_code=409, detail="Skill already installed")
        raise HTTPException(status_code=500, detail=f"Installation failed: {err_msg}")
