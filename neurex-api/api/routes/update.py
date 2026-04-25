"""
api/routes/update.py
Self-update system for Neurex.

Checks GitHub Releases for new versions and triggers a Docker image pull
in the background. The frontend polls /api/update/status to show the
notification badge, then reloads to activate the new version.
"""
from __future__ import annotations
import asyncio
import os
import structlog
from fastapi import APIRouter, Depends, BackgroundTasks
from api.routes.auth import require_role, UserRole

router = APIRouter(prefix="/api/update", tags=["update"])
log = structlog.get_logger()

CURRENT_VERSION = os.getenv("NEUREX_VERSION", "0.1.0")
GITHUB_REPO     = os.getenv("NEUREX_GITHUB_REPO", "sickn33/neurex")

# In-memory state (reset on process restart)
_update_state: dict = {
    "latest_version": None,
    "update_available": False,
    "update_ready": False,      # True once images are pulled
    "pulling": False,
    "error": None,
}


def _parse_semver(v: str) -> tuple[int, ...]:
    """Parse 'v1.2.3' or '1.2.3' into a comparable tuple."""
    return tuple(int(x) for x in v.lstrip("v").split(".")[:3])


async def _fetch_latest_version() -> str | None:
    """Hit the GitHub Releases API and return the latest tag name."""
    import httpx
    try:
        async with httpx.AsyncClient(timeout=5) as client:
            resp = await client.get(
                f"https://api.github.com/repos/{GITHUB_REPO}/releases/latest",
                headers={"Accept": "application/vnd.github.v3+json"},
            )
            resp.raise_for_status()
            return resp.json().get("tag_name")
    except Exception as e:
        log.warning("update.check_failed", error=str(e))
        return None


async def _pull_images():
    """Pull updated Docker images in the background."""
    _update_state["pulling"] = True
    _update_state["error"]   = None
    log.info("update.pulling_images")
    try:
        proc = await asyncio.create_subprocess_exec(
            "docker", "compose", "pull",
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.STDOUT,
        )
        stdout, _ = await asyncio.wait_for(proc.communicate(), timeout=300)
        if proc.returncode == 0:
            _update_state["update_ready"] = True
            log.info("update.images_ready")
        else:
            _update_state["error"] = stdout.decode(errors="replace")[-500:]
            log.error("update.pull_failed", rc=proc.returncode)
    except asyncio.TimeoutError:
        _update_state["error"] = "Image pull timed out after 5 minutes."
        log.error("update.pull_timeout")
    finally:
        _update_state["pulling"] = False


@router.get("/check")
async def check_for_updates():
    """
    Poll GitHub Releases and compare against NEUREX_VERSION env var.
    Called by the frontend on load and every 30 minutes.
    """
    latest = await _fetch_latest_version()
    if latest:
        _update_state["latest_version"] = latest
        try:
            _update_state["update_available"] = (
                _parse_semver(latest) > _parse_semver(CURRENT_VERSION)
            )
        except ValueError:
            _update_state["update_available"] = False

    return {
        "current_version": CURRENT_VERSION,
        "latest_version":  _update_state["latest_version"],
        "update_available": _update_state["update_available"],
        "update_ready":    _update_state["update_ready"],
        "pulling":         _update_state["pulling"],
    }


@router.get("/status")
async def get_update_status():
    """Lightweight status poll — no network call, returns cached state."""
    return {
        "current_version": CURRENT_VERSION,
        **_update_state,
    }


@router.post("/apply")
async def apply_update(
    background_tasks: BackgroundTasks,
    _=Depends(require_role(UserRole.ADMIN)),
):
    """
    Trigger a background image pull. ADMIN only.
    The user must reload the page/container after this completes.
    """
    if _update_state["pulling"]:
        return {"status": "already_pulling"}
    if not _update_state["update_available"]:
        return {"status": "no_update_available"}

    background_tasks.add_task(_pull_images)
    return {"status": "pulling_started"}
