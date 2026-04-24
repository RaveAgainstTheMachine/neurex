"""
core/memory/chunker.py
AST-aware code chunking using tree-sitter.
For code files: chunks at function/class boundaries.
For prose files (md, txt): sliding window with sentence awareness.
"""
from __future__ import annotations
import hashlib
from pathlib import Path
from typing import NamedTuple

import structlog

log = structlog.get_logger()

# tree-sitter language map
LANG_MAP = {
    ".py":   "python",
    ".ts":   "typescript",
    ".tsx":  "tsx",
    ".js":   "javascript",
    ".jsx":  "javascript",
    ".go":   "go",
    ".rs":   "rust",
    ".java": "java",
    ".cpp":  "cpp",
    ".c":    "c",
}

PROSE_EXTENSIONS = {".md", ".txt", ".yaml", ".yml", ".toml", ".json"}

MAX_CHUNK_CHARS = 1500
OVERLAP_CHARS   = 200


def chunk_file(path: Path) -> list[dict]:
    """
    Returns a list of chunk dicts:
      {
        "id":       str,       # stable hash of path + offset
        "text":     str,       # the chunk text
        "metadata": dict,      # file, language, start_line, end_line, symbol
      }
    """
    try:
        source = path.read_text(errors="replace")
    except Exception as e:
        log.warning("chunker.read_error", path=str(path), error=str(e))
        return []

    ext = path.suffix.lower()

    if ext in LANG_MAP:
        return _ast_chunks(source, path, LANG_MAP[ext])
    elif ext in PROSE_EXTENSIONS:
        return _sliding_window_chunks(source, path)
    return []


def _ast_chunks(source: str, path: Path, language: str) -> list[dict]:
    """Chunk at function/class/method boundaries using tree-sitter."""
    try:
        from tree_sitter_languages import get_language, get_parser
        lang   = get_language(language)
        parser = get_parser(language)
    except Exception as e:
        log.warning("chunker.ts_unavailable", lang=language, error=str(e))
        return _sliding_window_chunks(source, path)

    tree  = parser.parse(source.encode())
    lines = source.splitlines(keepends=True)
    chunks = []

    # Node types that represent top-level declarations
    TOP_LEVEL_TYPES = {
        "function_definition", "class_definition",       # Python
        "function_declaration", "class_declaration",     # JS/TS
        "method_definition", "arrow_function",           # JS/TS
        "impl_item", "fn_item", "struct_item",           # Rust
        "function_declaration",                          # Go
    }

    def walk(node):
        if node.type in TOP_LEVEL_TYPES:
            start = node.start_point[0]
            end   = node.end_point[0]
            text  = "".join(lines[start : end + 1])

            # Split oversized nodes
            for sub_text, sub_start in _split_long(text, start):
                chunks.append(_make_chunk(sub_text, path, language, sub_start, sub_start + sub_text.count("\n")))
        else:
            for child in node.children:
                walk(child)

    walk(tree.root_node)

    # If no top-level nodes found, fall back
    if not chunks:
        return _sliding_window_chunks(source, path)

    return chunks


def _sliding_window_chunks(source: str, path: Path) -> list[dict]:
    chunks = []
    start = 0
    lines = source.splitlines(keepends=True)
    current, current_start = [], 0

    for i, line in enumerate(lines):
        current.append(line)
        current_text = "".join(current)
        if len(current_text) >= MAX_CHUNK_CHARS:
            chunks.append(_make_chunk(current_text, path, "prose", current_start, i))
            # Overlap: keep last N chars
            overlap_text = current_text[-OVERLAP_CHARS:]
            current = [overlap_text]
            current_start = i

    if current:
        chunks.append(_make_chunk("".join(current), path, "prose", current_start, len(lines)))

    return chunks


def _make_chunk(text: str, path: Path, language: str, start_line: int, end_line: int, symbol: str = "") -> dict:
    chunk_id = hashlib.md5(f"{path}:{start_line}:{text[:50]}".encode()).hexdigest()[:12]
    return {
        "id":   chunk_id,
        "text": text.strip(),
        "metadata": {
            "file":       str(path),
            "language":   language,
            "start_line": start_line,
            "end_line":   end_line,
            "symbol":     symbol,
        },
    }


def _split_long(text: str, start_line: int):
    """Yield (sub_text, start_line) pairs for oversized chunks."""
    lines = text.splitlines(keepends=True)
    current, current_start = [], start_line
    for i, line in enumerate(lines):
        current.append(line)
        if len("".join(current)) >= MAX_CHUNK_CHARS:
            yield "".join(current), current_start
            current = []
            current_start = start_line + i + 1
    if current:
        yield "".join(current), current_start
