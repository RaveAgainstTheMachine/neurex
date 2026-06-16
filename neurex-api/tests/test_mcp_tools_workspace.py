from unittest.mock import AsyncMock, patch

import pytest

from core.mcp.tools.workspace import analyze_project_structure, deep_clean


@pytest.fixture
def mock_workspace(tmp_path, monkeypatch):
    monkeypatch.setattr("core.mcp.tools.workspace.WORKSPACE_PATH", str(tmp_path))
    return tmp_path

@pytest.mark.asyncio
async def test_deep_clean(mock_workspace):
    # Setup some fake cache dirs and files
    (mock_workspace / "__pycache__").mkdir()
    (mock_workspace / "__pycache__" / "test.pyc").touch()
    
    (mock_workspace / "some_dir").mkdir()
    (mock_workspace / "some_dir" / ".pytest_cache").mkdir()
    
    mock_proc = AsyncMock()
    mock_proc.communicate.return_value = (b"cleaned file", b"")
    
    with patch("asyncio.create_subprocess_exec", return_value=mock_proc) as mock_exec:
        res = await deep_clean()
        assert "__pycache__" in res
        assert ".pytest_cache" in res
        assert "Git cleaned: cleaned file" in res
        assert "Applied ruff fixes" in res
        assert mock_exec.call_count == 2 # git and ruff
        
        # Verify removal
        assert not (mock_workspace / "__pycache__").exists()
        assert not (mock_workspace / "some_dir" / ".pytest_cache").exists()

@pytest.mark.asyncio
async def test_deep_clean_empty(mock_workspace):
    mock_proc = AsyncMock()
    mock_proc.communicate.return_value = (b"", b"")
    with patch("asyncio.create_subprocess_exec", return_value=mock_proc):
        res = await deep_clean()
        assert "Applied ruff fixes" in res # Ruff always runs if it doesn't throw
        
    with patch("asyncio.create_subprocess_exec", side_effect=Exception("not found")):
        res2 = await deep_clean()
        assert res2 == "Workspace is already clean."

@pytest.mark.asyncio
async def test_analyze_project_structure(mock_workspace):
    (mock_workspace / "package.json").touch()
    (mock_workspace / "pyproject.toml").touch()
    (mock_workspace / "Cargo.toml").touch()
    (mock_workspace / "src").mkdir()
    (mock_workspace / ".git").mkdir()
    
    res = await analyze_project_structure()
    assert "src" in res
    assert ".git" not in res # Ignores . dirs
    assert "Node.js/TypeScript" in res
    assert "Python" in res
    assert "Rust" in res
