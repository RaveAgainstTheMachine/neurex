from unittest.mock import patch

import pytest

from core.skills.manager import SkillManager


@pytest.fixture
def manager(tmp_path):
    with patch("core.skills.manager.os.getenv", return_value=str(tmp_path)):
        return SkillManager()

def test_list_available(manager, tmp_path):
    skill_dir = tmp_path / "test_skill"
    skill_dir.mkdir()
    (skill_dir / "manifest.json").write_text('{"name": "test_skill", "description": "desc", "version": "1.0", "tools": [{"function": {"name": "test_tool"}}]}')
    
    res = manager.list_available()
    assert len(res) == 1
    assert res[0]["name"] == "test_skill"
    assert res[0]["type"] == "functional"

def test_get_skill_details(manager, tmp_path):
    skill_dir = tmp_path / "test_skill"
    skill_dir.mkdir()
    (skill_dir / "manifest.json").write_text('{"name": "test_skill", "author": "dev"}')
    
    res = manager.get_skill_details("test_skill")
    assert res["name"] == "test_skill"
    assert res["author"] == "dev"

def test_get_enabled_tools_and_get_skill_for_tool(manager, tmp_path):
    skill_dir = tmp_path / "test_skill"
    skill_dir.mkdir()
    (skill_dir / "manifest.json").write_text('{"tools": [{"function": {"name": "test_tool"}}]}')
    
    tools = manager.get_enabled_tools()
    assert len(tools) == 1
    
    skill_name = manager.get_skill_for_tool("test_tool")
    assert skill_name == "test_skill"

def test_delete_skill(manager, tmp_path):
    skill_dir = tmp_path / "test_skill"
    skill_dir.mkdir()
    
    assert manager.delete_skill("test_skill") is True
    assert not skill_dir.exists()

def test_fetch_curated_list(manager):
    res = manager.fetch_curated_list()
    assert len(res) > 0
    assert res[0]["id"] == "web-search" # fallback

@pytest.mark.asyncio
async def test_execute_skill_tool(manager, tmp_path):
    skill_dir = tmp_path / "test_skill"
    skill_dir.mkdir()
    handler_py = skill_dir / "handler.py"
    handler_py.write_text("async def handle(tool, args):\n    return 'success'")
    
    res = await manager.execute_skill_tool("test_skill", "test_tool", {})
    assert res == "success"

def test_install_from_git(manager, tmp_path):
    with patch("subprocess.run") as mock_run:
        with patch("shutil.copytree"):
            # Mock tempfile for subpath logic
            with patch("tempfile.TemporaryDirectory") as mock_temp:
                temp_git_dir = tmp_path / "temp_git"
                mock_temp.return_value.__enter__.return_value = str(temp_git_dir)
                
                # normal git clone
                manager.install_from_git("https://github.com/user/repo.git")
                mock_run.assert_called_with(["git", "clone", "--", "https://github.com/user/repo.git", str(manager.SKILLS_DIR / "repo")], check=True)
                
                # github tree
                (temp_git_dir / "subfolder").mkdir(parents=True, exist_ok=True)
                manager.install_from_git("https://github.com/user/repo/tree/main/subfolder")
                mock_run.assert_called_with(["git", "clone", "--depth", "1", "--", "https://github.com/user/repo", str(temp_git_dir)], check=True)

def test_load_metadata_markdown(manager, tmp_path):
    skill_dir = tmp_path / "md_skill"
    skill_dir.mkdir()
    (skill_dir / "SKILL.md").write_text('''---
name: md_skill_test
description: testing
version: 1.0.0
author: dev
---
Instructions go here
''')
    
    res = manager._load_metadata(skill_dir)
    assert res["name"] == "md_skill_test"
    assert res["description"] == "testing"
    assert res["author"] == "dev"
    assert res["version"] == "1.0.0"
    assert res["instructions"] == "Instructions go here"
