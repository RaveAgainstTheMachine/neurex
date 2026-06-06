"""
Unit tests for the Bidirectional LSP Context Router.
Verifies semantic operations (go to definition, find references, hover, diagnostics)
using robust mock assertions.
"""

from __future__ import annotations

from unittest.mock import AsyncMock, patch

import pytest

from core.intelligence.lsp_router import (
    lsp_find_references,
    lsp_get_diagnostics,
    lsp_get_hover,
    lsp_go_to_definition,
)
from core.languages.lsp_manager import diagnostic_tracker


@pytest.fixture
def mock_workspace(tmp_path, monkeypatch):
    """Create a temporary test workspace and mock the get_workspace utility."""
    ws = (tmp_path / "workspace").resolve()
    ws.mkdir()

    # Create sample files
    hello_file = ws / "hello.py"
    hello_file.write_text("def my_func():\n    pass\n\nmy_func()\n", encoding="utf-8")

    # Mock get_workspace to return this tmp path
    import api.routes.files as api_files
    import core.intelligence.lsp_router as lsp_router

    monkeypatch.setattr(api_files, "get_workspace", lambda: ws)
    monkeypatch.setattr(lsp_router, "get_workspace", lambda: ws)

    return ws


@pytest.mark.asyncio
async def test_lsp_go_to_definition(mock_workspace):
    """Test finding definition of a symbol with mocked LSP server response."""
    mock_session = AsyncMock()
    mock_session.write = AsyncMock()

    # Mock standard LSP definition response
    mock_response = {
        "result": {
            "uri": (mock_workspace / "hello.py").as_uri(),
            "range": {"start": {"line": 0, "character": 4}, "end": {"line": 0, "character": 11}},
        }
    }
    mock_session.send_request.return_value = mock_response

    with patch("core.languages.lsp_manager.lsp_manager.get_session", return_value=mock_session):
        res = await lsp_go_to_definition("hello.py", line=4, col=1)

        assert res["found"] is True
        assert len(res["definitions"]) == 1
        defn = res["definitions"][0]
        assert defn["file"] == "hello.py"
        assert defn["line"] == 1
        assert defn["column"] == 5
        assert "def my_func():" in defn["snippet"]


@pytest.mark.asyncio
async def test_lsp_find_references(mock_workspace):
    """Test querying references with mocked LSP server response."""
    mock_session = AsyncMock()
    mock_session.write = AsyncMock()

    # Mock references response from LSP
    mock_response = {
        "result": [
            {
                "uri": (mock_workspace / "hello.py").as_uri(),
                "range": {
                    "start": {"line": 0, "character": 4},
                    "end": {"line": 0, "character": 11},
                },
            },
            {
                "uri": (mock_workspace / "hello.py").as_uri(),
                "range": {"start": {"line": 3, "character": 0}, "end": {"line": 3, "character": 7}},
            },
        ]
    }
    mock_session.send_request.return_value = mock_response

    with patch("core.languages.lsp_manager.lsp_manager.get_session", return_value=mock_session):
        res = await lsp_find_references("hello.py", line=1, col=5)

        assert res["found"] is True
        assert len(res["references"]) == 2

        ref1 = res["references"][0]
        assert ref1["file"] == "hello.py"
        assert ref1["line"] == 1
        assert "def my_func():" in ref1["snippet"]

        ref2 = res["references"][1]
        assert ref2["file"] == "hello.py"
        assert ref2["line"] == 4
        assert "my_func()" in ref2["snippet"]


@pytest.mark.asyncio
async def test_lsp_get_hover(mock_workspace):
    """Test fetching hover documentation signature details with mocked LSP."""
    mock_session = AsyncMock()
    mock_session.write = AsyncMock()

    mock_response = {
        "result": {
            "contents": {
                "kind": "markdown",
                "value": "```python\ndef my_func()\n```\nSample function docstring.",
            }
        }
    }
    mock_session.send_request.return_value = mock_response

    with patch("core.languages.lsp_manager.lsp_manager.get_session", return_value=mock_session):
        res = await lsp_get_hover("hello.py", line=4, col=2)

        assert res["found"] is True
        assert "def my_func()" in res["markdown"]
        assert "docstring" in res["markdown"]


@pytest.mark.asyncio
async def test_lsp_get_diagnostics(mock_workspace):
    """Test retrieving stored compiler diagnostics for a workspace file."""
    # Update diagnostic tracker directly
    file_uri = (mock_workspace / "hello.py").as_uri()
    mock_diagnostics = [
        {
            "severity": 1,  # Error
            "message": "Undefined variable 'x'",
            "range": {"start": {"line": 3, "character": 0}, "end": {"line": 3, "character": 1}},
        },
        {
            "severity": 2,  # Warning
            "message": "Unused import 'sys'",
            "range": {"start": {"line": 1, "character": 0}, "end": {"line": 1, "character": 3}},
        },
    ]

    with patch(
        "core.collaboration.presence.presence_manager.broadcast_global", new_callable=AsyncMock
    ):
        diagnostic_tracker.update(file_uri, mock_diagnostics)

        res = lsp_get_diagnostics("hello.py")
        assert res["file"] == "hello.py"
        assert len(res["diagnostics"]) == 2
        assert res["error_count"] == 1
        assert res["diagnostics"][0]["message"] == "Undefined variable 'x'"
