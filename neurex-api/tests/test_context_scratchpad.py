import json
from unittest.mock import patch

import pytest

from core.context.scratchpad import clear_scratchpad, get_scratchpad, set_scratchpad_value


@pytest.fixture
def mock_dir(tmp_path):
    with patch("core.context.scratchpad.SCRATCHPAD_DIR", tmp_path):
        yield tmp_path

@pytest.mark.asyncio
async def test_set_scratchpad_value(mock_dir):
    res = await set_scratchpad_value("conv-123", "key1", "val1")
    assert "✅" in res
    
    file_path = mock_dir / "conv-123.json"
    assert file_path.exists()
    
    with open(file_path) as f:
        data = json.load(f)
        assert data["key1"] == "val1"
        
    res = await set_scratchpad_value("conv-123", "key2", "val2")
    with open(file_path) as f:
        data = json.load(f)
        assert data["key1"] == "val1"
        assert data["key2"] == "val2"

@pytest.mark.asyncio
async def test_set_scratchpad_value_invalid_id():
    with pytest.raises(ValueError, match="Invalid conversation_id"):
        await set_scratchpad_value("invalid/id", "key1", "val1")

@pytest.mark.asyncio
async def test_set_scratchpad_value_path_traversal(mock_dir):
    with patch("os.path.realpath", side_effect=lambda x: "/etc/passwd" if "conv" in x else str(mock_dir)):
        with pytest.raises(ValueError, match="Security violation"):
            await set_scratchpad_value("conv-123", "key1", "val1")

@pytest.mark.asyncio
async def test_get_scratchpad(mock_dir):
    # Empty
    data = await get_scratchpad("conv-123")
    assert data == {}
    
    # Existing
    await set_scratchpad_value("conv-123", "key1", "val1")
    data = await get_scratchpad("conv-123")
    assert data == {"key1": "val1"}

@pytest.mark.asyncio
async def test_get_scratchpad_invalid_id():
    data = await get_scratchpad("invalid/id")
    assert data == {}

@pytest.mark.asyncio
async def test_get_scratchpad_path_traversal(mock_dir):
    with patch("os.path.realpath", side_effect=lambda x: "/etc/passwd" if "conv" in x else str(mock_dir)):
        data = await get_scratchpad("conv-123")
        assert data == {}

@pytest.mark.asyncio
async def test_clear_scratchpad(mock_dir):
    await set_scratchpad_value("conv-123", "key1", "val1")
    
    res = await clear_scratchpad("conv-123")
    assert "✅" in res
    
    data = await get_scratchpad("conv-123")
    assert data == {}

@pytest.mark.asyncio
async def test_clear_scratchpad_invalid_id():
    res = await clear_scratchpad("invalid/id")
    assert "❌" in res

@pytest.mark.asyncio
async def test_clear_scratchpad_path_traversal(mock_dir):
    with patch("os.path.realpath", side_effect=lambda x: "/etc/passwd" if "conv" in x else str(mock_dir)):
        res = await clear_scratchpad("conv-123")
        assert "❌" in res
