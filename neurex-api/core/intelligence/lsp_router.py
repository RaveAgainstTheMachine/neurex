"""
core/intelligence/lsp_router.py
Multiplexes semantic LSP operations (Definitions, References, Hovers, Diagnostics) 
to active language server sessions. Exposes them directly for agentic invocation.
"""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any

import structlog

from api.routes.files import get_workspace
from core.languages.lsp_manager import diagnostic_tracker, lsp_manager

log = structlog.get_logger()

# Map file extensions to language servers
LANG_MAP: dict[str, str] = {
    ".py": "python",
    ".ts": "typescript",
    ".tsx": "typescript",
    ".js": "javascript",
    ".jsx": "javascript",
    ".rs": "rust",
    ".go": "go",
    ".c": "c",
    ".cpp": "cpp",
}

def get_session_for_file(file_path: str) -> tuple[Path, str, str]:
    """Resolves session, absolute file path, relative file path, and language ID."""
    workspace = get_workspace()
    if not workspace:
        raise ValueError("No active workspace found")
    
    safe_root = os.path.realpath(str(workspace))
    target = os.path.realpath(os.path.join(safe_root, file_path))
    safe_prefix = safe_root if safe_root.endswith(os.sep) else safe_root + os.sep
    if target == safe_root:
        pass
    elif target.startswith(safe_prefix):
        pass
    else:
        raise PermissionError(f"Path traversal attempt blocked: {file_path!r} resolves outside workspace.")
        
    abs_path = Path(target)
    rel_path = str(abs_path.relative_to(workspace))
    
    ext = abs_path.suffix.lower()
    lang = LANG_MAP.get(ext)
    if not lang:
        raise ValueError(f"Unsupported file type '{ext}' for LSP operations")
        
    loop = lsp_manager.sessions
    # Synchronously look up or try to get session (since session startup is async, we do startup inline)
    return abs_path, rel_path, lang


async def ensure_file_opened(session: Any, abs_path: Path, uri: str, lang: str):
    """Notify the LSP that the file is open to populate its index correctly."""
    try:
        content = abs_path.read_text(encoding="utf-8", errors="replace")  # lgtm [py/path-injection]
    except Exception:
        content = ""
        
    notification = {
        "jsonrpc": "2.0",
        "method": "textDocument/didOpen",
        "params": {
            "textDocument": {
                "uri": uri,
                "languageId": lang,
                "version": 1,
                "text": content
            }
        }
    }
    body = json.dumps(notification).encode('utf-8')
    header = f"Content-Length: {len(body)}\r\n\r\n".encode('ascii')
    await session.write(header + body)

def extract_snippet(file_abs_path: Path, line_1: int) -> str:
    """Extracts a single line snippet from a file (1-indexed)."""
    if not file_abs_path.exists():
        return ""
    try:
        lines = file_abs_path.read_text(encoding="utf-8", errors="replace").splitlines()
        if 1 <= line_1 <= len(lines):
            return lines[line_1 - 1].strip()
    except Exception:
        pass
    return ""

async def lsp_go_to_definition(file_path: str, line: int, col: int) -> dict:
    """
    Find coordinates and line snippets of symbol definition.
    Inputs are 1-indexed (line, column).
    """
    try:
        abs_path, rel_path, lang = get_session_for_file(file_path)
        workspace = get_workspace()
        session = await lsp_manager.get_session(lang, str(workspace))
        
        uri = abs_path.as_uri()
        await ensure_file_opened(session, abs_path, uri, lang)
        
        # LSP uses 0-indexed coordinates
        params = {
            "textDocument": {"uri": uri},
            "position": {"line": max(0, line - 1), "character": max(0, col - 1)}
        }
        
        response = await session.send_request("textDocument/definition", params)
        result = response.get("result")
        if not result:
            return {"found": False, "message": "No definition found"}
            
        # Standardize result: Location or Location[]
        locations = result if isinstance(result, list) else [result]
        definitions = []
        
        for loc in locations:
            # Handle standard location or LocationLink
            loc_uri = loc.get("uri") or loc.get("targetUri")
            if not loc_uri:
                continue
                
            # Parse target coordinates
            target_range = loc.get("range") or loc.get("targetSelectionRange")
            start = target_range["start"]
            target_line = start["line"] + 1
            target_col = start["character"] + 1
            
            # Resolve absolute path and relative path
            from urllib.parse import unquote
            target_abs = Path(unquote(loc_uri.replace("file://", ""))).resolve()
            target_rel = str(target_abs.relative_to(workspace)) if target_abs.is_relative_to(workspace) else str(target_abs)
            
            snippet = extract_snippet(target_abs, target_line)
            
            definitions.append({
                "file": target_rel,
                "line": target_line,
                "column": target_col,
                "snippet": snippet
            })
            
        return {"found": True, "definitions": definitions}
        
    except Exception as e:
        log.error("lsp.definition_failed", error=str(e))
        return {"found": False, "error": str(e)}

async def lsp_find_references(file_path: str, line: int, col: int) -> dict:
    """
    Find all reference locations and snippets for the symbol.
    Inputs are 1-indexed.
    """
    try:
        abs_path, rel_path, lang = get_session_for_file(file_path)
        workspace = get_workspace()
        session = await lsp_manager.get_session(lang, str(workspace))
        
        uri = abs_path.as_uri()
        await ensure_file_opened(session, abs_path, uri, lang)
        
        params = {
            "textDocument": {"uri": uri},
            "position": {"line": max(0, line - 1), "character": max(0, col - 1)},
            "context": {"includeDeclaration": True}
        }
        
        response = await session.send_request("textDocument/references", params)
        result = response.get("result") or []
        references = []
        
        for loc in result:
            loc_uri = loc.get("uri")
            if not loc_uri:
                continue
                
            start = loc["range"]["start"]
            target_line = start["line"] + 1
            target_col = start["character"] + 1
            
            from urllib.parse import unquote
            target_abs = Path(unquote(loc_uri.replace("file://", ""))).resolve()
            target_rel = str(target_abs.relative_to(workspace)) if target_abs.is_relative_to(workspace) else str(target_abs)
            
            snippet = extract_snippet(target_abs, target_line)
            
            references.append({
                "file": target_rel,
                "line": target_line,
                "column": target_col,
                "snippet": snippet
            })
            
        return {"found": len(references) > 0, "references": references}
        
    except Exception as e:
        log.error("lsp.references_failed", error=str(e))
        return {"found": False, "error": str(e)}

async def lsp_get_hover(file_path: str, line: int, col: int) -> dict:
    """
    Retrieve semantic signature under the cursor (methods, docstrings, type definitions).
    Inputs are 1-indexed.
    """
    try:
        abs_path, rel_path, lang = get_session_for_file(file_path)
        workspace = get_workspace()
        session = await lsp_manager.get_session(lang, str(workspace))
        
        uri = abs_path.as_uri()
        await ensure_file_opened(session, abs_path, uri, lang)
        
        params = {
            "textDocument": {"uri": uri},
            "position": {"line": max(0, line - 1), "character": max(0, col - 1)}
        }
        
        response = await session.send_request("textDocument/hover", params)
        result = response.get("result")
        if not result:
            return {"found": False, "message": "No hover context found"}
            
        # Parse hover contents (can be string, MarkupContent, or MarkedString[])
        contents = result.get("contents", "")
        hover_text = ""
        
        if isinstance(contents, dict):
            # MarkupContent
            hover_text = contents.get("value", "")
        elif isinstance(contents, list):
            hover_text = "\n".join([c if isinstance(c, str) else c.get("value", "") for c in contents])
        else:
            hover_text = str(contents)
            
        return {
            "found": True,
            "markdown": hover_text,
            "range": result.get("range")
        }
        
    except Exception as e:
        log.error("lsp.hover_failed", error=str(e))
        return {"found": False, "error": str(e)}

def lsp_get_diagnostics(file_path: str) -> dict:
    """
    Query current language server compilation errors or warnings for the file.
    """
    try:
        # Diagnostic tracker maps clean relative paths
        diagnostics = diagnostic_tracker.get_for_path(file_path)
        return {
            "file": file_path,
            "diagnostics": diagnostics,
            "error_count": len([d for d in diagnostics if d.get("severity") == 1]) # Severity 1 is Error in LSP
        }
    except Exception as e:
        log.error("lsp.diagnostics_failed", error=str(e))
        return {"error": str(e)}
