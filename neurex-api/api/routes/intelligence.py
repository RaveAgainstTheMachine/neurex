"""
api/routes/intelligence.py
REST router for language intelligence and code comprehension capabilities.
"""

from __future__ import annotations

import os
from pathlib import Path

import structlog
from fastapi import APIRouter, Depends, HTTPException

from api.routes.auth import get_current_user
from api.routes.files import get_workspace
from core.intelligence.ast_helper import get_ast_bounds

log = structlog.get_logger()
router = APIRouter()


@router.get("/ast-bounds")
async def get_bounds(
    path: str,
    line: int,
    column: int,
    user=Depends(get_current_user),
) -> dict[str, int]:
    """
    Computes class, method, or function boundaries for target coordinates
    using the Tree-Sitter AST parser.
    """
    try:
        workspace_path = get_workspace()
        if not workspace_path:
            raise HTTPException(status_code=400, detail="No active workspace found")

        safe_root = os.path.realpath(str(workspace_path))
        target = os.path.realpath(os.path.join(safe_root, path))
        safe_prefix = safe_root if safe_root.endswith(os.sep) else safe_root + os.sep

        # Security check: ensure resolved path is contained within active workspace
        if target != safe_root:
            if not target.startswith(safe_prefix):
                log.warning("ast.out_of_bounds_access", path=path, workspace=str(workspace_path))
                raise PermissionError("Path traversal blocked")

        file_path = Path(target)
        start, end = get_ast_bounds(file_path, line, column)
        return {"start_line": start, "end_line": end}

    except HTTPException:
        raise
    except Exception as e:
        log.error("ast.endpoint_failed", path=path, error=str(e))
        raise HTTPException(status_code=500, detail="Failed to get AST boundaries. Check API logs.")
