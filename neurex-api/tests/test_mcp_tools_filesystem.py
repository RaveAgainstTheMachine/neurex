
import pytest

from core.mcp.tools.filesystem import (
    _safe_path,
    _validate_content_for_placeholders,
    apply_diff,
    commit_staging,
    delete_file,
    get_staging_root,
    get_trash_root,
    list_directory,
    list_staging,
    read_file,
    workspace_path_var,
    write_file,
)


@pytest.fixture
def workspace(tmp_path):
    token = workspace_path_var.set(str(tmp_path))
    yield tmp_path
    workspace_path_var.reset(token)

def test_safe_path(workspace):
    # Valid
    p = _safe_path("test.txt")
    assert p.name == "test.txt"
    assert p.parent == workspace

    # Path traversal
    with pytest.raises(PermissionError):
        _safe_path("../outside.txt")
        
    # Trash access
    trash = workspace / ".neurex" / "trash"
    trash.mkdir(parents=True)
    with pytest.raises(PermissionError):
        _safe_path(".neurex/trash/test.txt")

def test_validate_placeholders():
    assert _validate_content_for_placeholders("a.txt", "OK code") is None
    
    err = _validate_content_for_placeholders("a.ts", "// TODO: implement")
    assert "MUTATION_REJECTED" in err
    
    err = _validate_content_for_placeholders("a.py", "<agent placeholder>")
    assert "MUTATION_REJECTED" in err

@pytest.mark.asyncio
async def test_read_file(workspace):
    f = workspace / "test.txt"
    f.write_text("hello")
    res = await read_file("test.txt")
    assert res == "hello"
    
    # Missing
    assert "Error: file not found" in await read_file("missing.txt")
    
    # Truncate
    large = "a" * 50_000
    f.write_text(large)
    res = await read_file("test.txt")
    assert "truncated" in res
    assert len(res) < 50_000

@pytest.mark.asyncio
async def test_write_file(workspace):
    res = await write_file("test.txt", "hello", "limited")
    assert "OK" in res
    assert (workspace / "test.txt").read_text() == "hello"
    
    # Restricted
    res = await write_file("test.txt", "hello", "restricted")
    assert "APPROVAL_REQUIRED" in res
    
    # Staging
    res = await write_file("staged.txt", "hello staging", "staging")
    assert "OK" in res
    assert not (workspace / "staged.txt").exists()
    assert (get_staging_root() / "staged.txt").exists()

@pytest.mark.asyncio
async def test_delete_file(workspace):
    f = workspace / "del.txt"
    f.write_text("delete me")
    
    # Restricted
    assert "APPROVAL_REQUIRED" in await delete_file("del.txt", "restricted")
    
    # Normal
    res = await delete_file("del.txt", "limited")
    assert "OK" in res
    assert not f.exists()
    trash_files = list(get_trash_root().iterdir())
    assert len(trash_files) == 1
    assert "del.txt" in trash_files[0].name

@pytest.mark.asyncio
async def test_staging_workflow(workspace):
    f1 = workspace / "f1.txt"
    f1.write_text("orig1")
    
    f2 = workspace / "f2.txt"
    f2.write_text("orig2")
    
    # Modify f1 in staging
    await write_file("f1.txt", "mod1", "staging")
    
    # Delete f2 in staging
    await delete_file("f2.txt", "staging")
    
    # Add new f3 in staging
    await write_file("f3.txt", "new3", "staging")
    
    staged = await list_staging()
    assert len(staged) == 3
    
    # Commit
    await commit_staging()
    
    assert f1.read_text() == "mod1"
    assert not f2.exists()
    assert (workspace / "f3.txt").read_text() == "new3"

@pytest.mark.asyncio
async def test_apply_diff(workspace):
    f = workspace / "test.py"
    f.write_text("def a():\n    pass\n")
    
    res = await apply_diff("test.py", "def a():\n    pass", "def b():\n    pass", "limited")
    assert "OK" in res
    assert "def b():" in f.read_text()
    
    # Staging
    res = await apply_diff("test.py", "def b():\n    pass", "def c():\n    pass", "staging")
    assert "OK" in res
    assert "def b():" in f.read_text() # not changed
    assert "def c():" in (get_staging_root() / "test.py").read_text()

@pytest.mark.asyncio
async def test_list_directory(workspace):
    (workspace / "dir1").mkdir()
    (workspace / "f1.txt").write_text("a")
    res = await list_directory(".")
    assert "dir  dir1" in res
    assert "file  f1.txt" in res
