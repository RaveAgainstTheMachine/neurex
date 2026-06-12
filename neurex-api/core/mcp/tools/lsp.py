"""
core/mcp/tools/lsp.py
LSP semantic search tools exposed for agentic execution.
"""

from __future__ import annotations

import json

import structlog

from core.intelligence.lsp_router import (
    lsp_find_references as api_lsp_find_references,
)
from core.intelligence.lsp_router import (
    lsp_get_diagnostics as api_lsp_get_diagnostics,
)
from core.intelligence.lsp_router import (
    lsp_get_hover as api_lsp_get_hover,
)
from core.intelligence.lsp_router import (
    lsp_go_to_definition as api_lsp_go_to_definition,
)

log = structlog.get_logger()


async def lsp_go_to_definition(file_path: str, line: int, col: int) -> str:
    """
    Find coordinates and line snippets of a symbol's definition.
    Inputs are 1-indexed (line, column).
    """
    log.info("mcp.lsp_go_to_definition.start", file_path=file_path, line=line, col=col)
    try:
        result = await api_lsp_go_to_definition(file_path, line, col)
        return json.dumps(result, indent=2)
    except Exception as e:
        log.error("mcp.lsp_go_to_definition.failed", file_path=file_path, error=str(e))
        return json.dumps({"found": False, "error": str(e)}, indent=2)


async def lsp_find_references(file_path: str, line: int, col: int) -> str:
    """
    Find all reference locations and snippets for a symbol.
    Inputs are 1-indexed.
    """
    log.info("mcp.lsp_find_references.start", file_path=file_path, line=line, col=col)
    try:
        result = await api_lsp_find_references(file_path, line, col)
        return json.dumps(result, indent=2)
    except Exception as e:
        log.error("mcp.lsp_find_references.failed", file_path=file_path, error=str(e))
        return json.dumps({"found": False, "error": str(e)}, indent=2)


async def lsp_get_hover(file_path: str, line: int, col: int) -> str:
    """
    Retrieve semantic signature (methods, docstrings, type definitions) under the cursor.
    Inputs are 1-indexed.
    """
    log.info("mcp.lsp_get_hover.start", file_path=file_path, line=line, col=col)
    try:
        result = await api_lsp_get_hover(file_path, line, col)
        return json.dumps(result, indent=2)
    except Exception as e:
        log.error("mcp.lsp_get_hover.failed", file_path=file_path, error=str(e))
        return json.dumps({"found": False, "error": str(e)}, indent=2)


async def lsp_get_diagnostics(file_path: str) -> str:
    """
    Query current language server compilation errors or warnings for the file.
    """
    log.info("mcp.lsp_get_diagnostics.start", file_path=file_path)
    try:
        result = api_lsp_get_diagnostics(file_path)
        return json.dumps(result, indent=2)
    except Exception as e:
        log.error("mcp.lsp_get_diagnostics.failed", file_path=file_path, error=str(e))
        return json.dumps({"error": str(e)}, indent=2)
