from unittest.mock import patch

import pytest

from core.mcp.tools.skills_builder import create_skill, publish_skill


@pytest.fixture
def skills_dir(tmp_path):
    with patch("core.mcp.tools.skills_builder.SKILLS_DIR", str(tmp_path)):
        yield tmp_path

@pytest.mark.asyncio
async def test_create_skill_success(skills_dir):
    res = await create_skill("test_skill", "desc", "    print('ok')")
    assert "✅ Skill 'test_skill' created" in res
    assert (skills_dir / "test_skill").exists()
    assert (skills_dir / "test_skill" / "manifest.json").exists()
    assert (skills_dir / "test_skill" / "handler.py").exists()

@pytest.mark.asyncio
async def test_create_skill_already_exists(skills_dir):
    (skills_dir / "test_skill").mkdir()
    res = await create_skill("test_skill", "desc", "code")
    assert "already exists" in res

@pytest.mark.asyncio
async def test_create_skill_exception(skills_dir):
    with patch("pathlib.Path.mkdir", side_effect=Exception("boom")):
        res = await create_skill("test_skill", "desc", "code")
        assert "Failed to create skill" in res

@pytest.mark.asyncio
async def test_publish_skill_success(skills_dir):
    (skills_dir / "test_skill").mkdir()
    res = await publish_skill("test_skill")
    assert "published" in res

@pytest.mark.asyncio
async def test_publish_skill_not_found(skills_dir):
    res = await publish_skill("test_skill")
    assert "not found" in res
