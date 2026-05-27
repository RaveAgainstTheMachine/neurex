"""
core/intelligence/ast_helper.py
AST-aware coordinate extraction using tree-sitter.
Determines exact function, method, and class boundary ranges based on file extensions.
"""

from __future__ import annotations

import ast
from pathlib import Path
from typing import Any

import structlog

log = structlog.get_logger()

# Map file extensions to tree-sitter language keys
LANG_MAP: dict[str, str] = {
    ".py": "python",
    ".ts": "typescript",
    ".tsx": "tsx",
    ".js": "javascript",
    ".jsx": "javascript",
    ".go": "go",
    ".rs": "rust",
    ".java": "java",
    ".cpp": "cpp",
    ".c": "c",
}

# Node types that represent structural containers / declarations
TOP_LEVEL_TYPES: set[str] = {
    "function_definition",
    "class_definition",  # Python
    "function_declaration",
    "class_declaration",  # JS/TS
    "method_definition",
    "arrow_function",  # JS/TS
    "impl_item",
    "fn_item",
    "struct_item",  # Rust
    "function_declaration",  # Go
}


def find_node_at_position(node: Any, line: int, col: int) -> Any:
    """
    Finds the deepest (smallest) node containing the 0-indexed position (line, col).
    """
    if not (node.start_point <= (line, col) <= node.end_point):
        return None

    # Recurse into children for more specific nodes
    for child in node.children:
        found = find_node_at_position(child, line, col)
        if found is not None:
            return found

    return node


def get_ast_bounds(file_path: Path, line: int, column: int) -> tuple[int, int]:
    """
    Given a file path and a 1-indexed cursor position (line, column),
    returns the (start_line, end_line) 1-indexed boundaries of the surrounding structural symbol.
    If no structural boundary can be computed, returns (line, line).
    """
    try:
        try:
            import os

            from api.routes.files import get_workspace

            workspace = get_workspace()
            safe_root = os.path.realpath(str(workspace or "."))
            target = os.path.realpath(str(file_path))
        except Exception as e:
            log.error("ast.resolve_failed", path=str(file_path), error=str(e))
            return line, line

        safe_prefix = safe_root if safe_root.endswith(os.sep) else safe_root + os.sep
        if not target.startswith(safe_prefix):
            log.warning("ast.security_violation", path=str(file_path))
            raise ValueError("Path traversal blocked")

        safe_path = Path(target)

        if not safe_path.exists():
            log.warning("ast.file_not_found", path=str(safe_path))
            return line, line

        ext = safe_path.suffix.lower()
        if ext not in LANG_MAP:
            log.debug("ast.unsupported_extension", path=str(safe_path), ext=ext)
            return line, line

        try:
            source = safe_path.read_text(encoding="utf-8", errors="replace")
        except Exception as e:
            log.error("ast.read_failed", path=str(safe_path), error=str(e))
            return line, line

        # Handle Python files using standard ast module
        if ext == ".py":
            try:
                tree = ast.parse(source)
                candidate = None
                for node in ast.walk(tree):
                    if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
                        # Check if the line is within this node
                        if node.lineno <= line <= node.end_lineno:
                            # If we have no candidate, or this candidate is smaller (tighter)
                            if candidate is None or (
                                node.lineno >= candidate.lineno
                                and node.end_lineno <= candidate.end_lineno
                            ):
                                candidate = node
                if candidate:
                    return candidate.lineno, candidate.end_lineno
            except Exception as e:
                log.error("ast.python_parse_failed", path=str(safe_path), error=str(e))
            return line, line

        # Fallback to tree-sitter for other languages
        language = LANG_MAP[ext]
        parser = None
        try:
            from tree_sitter import Language, Parser

            if language in ("javascript", "typescript", "tsx"):
                import tree_sitter_javascript as tsjs

                parser = Parser(Language(tsjs.language()))
        except Exception as e:
            log.debug("ast.direct_ts_failed", lang=language, error=str(e))

        if parser is None:
            try:
                from tree_sitter_languages import get_parser

                parser = get_parser(language)
            except Exception as e:
                log.warning("ast.ts_setup_failed", lang=language, error=str(e))
                return line, line

        try:
            tree = parser.parse(source.encode("utf-8"))
            root = tree.root_node
        except Exception as e:
            log.error("ast.parse_failed", path=str(safe_path), error=str(e))
            return line, line

        # Convert 1-indexed position to 0-indexed position for tree-sitter
        target_line = max(0, line - 1)
        target_col = max(0, column - 1)

        node = find_node_at_position(root, target_line, target_col)
        if node is None:
            log.debug("ast.no_node_found", path=str(safe_path), line=line, col=column)
            return line, line

        # Traverse upward to find the closest logical structural boundary
        ancestor = node
        while ancestor is not None:
            if ancestor.type in TOP_LEVEL_TYPES:
                start_line_1 = ancestor.start_point[0] + 1
                end_line_1 = ancestor.end_point[0] + 1
                log.info(
                    "ast.bounds_found",
                    path=str(safe_path),
                    symbol_type=ancestor.type,
                    start=start_line_1,
                    end=end_line_1,
                )
                return start_line_1, end_line_1
            ancestor = ancestor.parent

        # Default fallback to the original line
        log.debug("ast.no_boundary_ancestor", path=str(safe_path), line=line)
        return line, line

    except ValueError:
        return line, line
