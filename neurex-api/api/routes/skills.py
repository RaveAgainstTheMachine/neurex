from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field

from api.routes.auth import UserRole, require_role
from core.skills.manager import SkillManager

router = APIRouter()
manager = SkillManager()


import json
import time


class SkillInstallRequest(BaseModel):
    url: str = Field(..., description="The Git repository URL or subpath URL")


class SkillPublishRequest(BaseModel):
    name: str = Field(..., description="The name of the skill")
    description: str = Field(..., description="A short description")
    url: str = Field(..., description="The Git repository URL")
    author: str = Field(..., description="The author's name")
    version: str = Field(..., description="Version string")
    category: str = Field("All", description="Marketplace category")


@router.get("/")
async def list_skills():
    """List all installed skills."""
    return manager.list_available()


@router.get("/curated")
async def list_curated():
    """Fetch the 'Awesome Skills' library from remote."""
    return manager.fetch_curated_list()


@router.get("/marketplace")
async def get_marketplace():
    """Fetch all discoverable marketplace plugins (curated + published)."""
    curated = manager.fetch_curated_list()
    
    mock_path = manager.SKILLS_DIR / ".marketplace_mock.json"
    published = []
    if mock_path.exists():
        try:
            with open(mock_path) as f:
                published = json.load(f)
        except Exception:
            pass
            
    combined = []
    seen_urls = set()
    
    for p in published:
        combined.append(p)
        seen_urls.add(p["url"])
        
    for c in curated:
        if c["url"] not in seen_urls:
            combined.append(c)
            
    return combined


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
        err_msg = str(e)
        if "already exists" in err_msg:
            raise HTTPException(status_code=409, detail="Skill already installed")
        raise HTTPException(status_code=500, detail=f"Installation failed: {err_msg}")


@router.post("/publish", dependencies=[Depends(require_role(UserRole.DEVELOPER))])
async def publish_skill(req: SkillPublishRequest):
    """Publish/register a new skill to the local marketplace catalog."""
    mock_path = manager.SKILLS_DIR / ".marketplace_mock.json"
    published = []
    if mock_path.exists():
        try:
            with open(mock_path) as f:
                published = json.load(f)
        except Exception:
            pass
            
    if any(p["url"] == req.url for p in published):
        raise HTTPException(status_code=409, detail="Skill repository already published")
        
    new_item = {
        "id": req.name.lower().replace(" ", "-"),
        "name": req.name,
        "description": req.description,
        "url": req.url,
        "author": req.author,
        "version": req.version,
        "category": req.category,
        "stars": 0,
        "enabled": True,
        "published_at": time.time()
    }
    
    published.append(new_item)
    try:
        with open(mock_path, "w") as f:
            json.dump(published, f, indent=2)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to persist plugin: {str(e)}")
        
    return {"status": "success", "skill": new_item}
