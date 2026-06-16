from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field

from api.routes.auth import UserRole, require_role
from core.skills.manager import SkillManager

router = APIRouter()
manager = SkillManager()


import time

import httpx
from sqlmodel import select

from core.skills.models import PluginHubItem
from core.task_graph import async_session


class SkillInstallRequest(BaseModel):
    url: str = Field(..., description="The Git repository URL or subpath URL")


class SkillPublishRequest(BaseModel):
    name: str = Field(..., description="The name of the skill")
    description: str = Field(..., description="A short description")
    url: str = Field(..., description="The Git repository URL")
    author: str = Field(..., description="The author's name")
    version: str = Field(..., description="Version string")
    category: str = Field("All", description="Marketplace category")
    plugin_type: str = Field("skill", description="Either 'skill' or 'mcp'")


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

    published = []
    async with async_session() as session:
        result = await session.exec(select(PluginHubItem))
        published = [p.model_dump() for p in result.all()]

    combined = []
    seen_urls = set()

    for p in published:
        p["is_official"] = False
        combined.append(p)
        seen_urls.add(p["url"])

    for c in curated:
        if c["url"] not in seen_urls:
            c["is_official"] = True
            c["plugin_type"] = "skill" # Curated ones are currently skills
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
    # Verify the URL is reachable
    try:
        async with httpx.AsyncClient() as client:
            resp = await client.get(req.url, follow_redirects=True, timeout=5.0)
            if resp.status_code >= 400:
                raise HTTPException(status_code=400, detail=f"Repository URL returned status {resp.status_code}")
    except httpx.RequestError as e:
        raise HTTPException(status_code=400, detail=f"Failed to reach repository URL: {str(e)}")

    async with async_session() as session:
        result = await session.exec(select(PluginHubItem).where(PluginHubItem.url == req.url))
        if result.first():
            raise HTTPException(status_code=409, detail="Skill repository already published")

        new_item = PluginHubItem(
            id=req.name.lower().replace(" ", "-"),
            name=req.name,
            description=req.description,
            url=req.url,
            author=req.author,
            version=req.version,
            category=req.category,
            plugin_type=req.plugin_type,
            stars=0,
            enabled=True,
            is_official=False,
            published_at=time.time(),
        )

        session.add(new_item)
        try:
            await session.commit()
            await session.refresh(new_item)
        except Exception as e:
            await session.rollback()
            raise HTTPException(status_code=500, detail=f"Failed to persist plugin: {str(e)}")

    return {"status": "success", "skill": new_item.model_dump()}
