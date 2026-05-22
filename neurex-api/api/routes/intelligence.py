"""
api/routes/intelligence.py
REST router for language intelligence and code comprehension capabilities.
"""

from __future__ import annotations

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
        file_path = (workspace_path / path).resolve()

        # Security check: ensure resolved path is contained within active workspace
        if not str(file_path).startswith(str(workspace_path.resolve())):
            log.warning("ast.out_of_bounds_access", path=path, workspace=str(workspace_path))
            raise HTTPException(status_code=403, detail="Access denied")

        start, end = get_ast_bounds(file_path, line, column)
        return {"start_line": start, "end_line": end}

    except HTTPException:
        raise
    except Exception as e:
        log.error("ast.endpoint_failed", path=path, error=str(e))
        raise HTTPException(status_code=500, detail=str(e))
