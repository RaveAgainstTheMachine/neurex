import json
from unittest.mock import AsyncMock, patch

import pytest

from core.mcp.tools.lsp import (
    lsp_find_references,
    lsp_get_diagnostics,
    lsp_get_hover,
    lsp_go_to_definition,
)


@pytest.mark.asyncio
async def test_lsp_go_to_definition():
    with patch("core.mcp.tools.lsp.api_lsp_go_to_definition", new_callable=AsyncMock) as mock_api:
        mock_api.return_value = {"found": True}
        res = await lsp_go_to_definition("test.py", 1, 1)
        assert json.loads(res)["found"] is True

        mock_api.side_effect = Exception("failed")
        res = await lsp_go_to_definition("test.py", 1, 1)
        assert json.loads(res)["found"] is False

@pytest.mark.asyncio
async def test_lsp_find_references():
    with patch("core.mcp.tools.lsp.api_lsp_find_references", new_callable=AsyncMock) as mock_api:
        mock_api.return_value = {"found": True}
        res = await lsp_find_references("test.py", 1, 1)
        assert json.loads(res)["found"] is True

        mock_api.side_effect = Exception("failed")
        res = await lsp_find_references("test.py", 1, 1)
        assert json.loads(res)["found"] is False

@pytest.mark.asyncio
async def test_lsp_get_hover():
    with patch("core.mcp.tools.lsp.api_lsp_get_hover", new_callable=AsyncMock) as mock_api:
        mock_api.return_value = {"found": True}
        res = await lsp_get_hover("test.py", 1, 1)
        assert json.loads(res)["found"] is True

        mock_api.side_effect = Exception("failed")
        res = await lsp_get_hover("test.py", 1, 1)
        assert json.loads(res)["found"] is False

@pytest.mark.asyncio
async def test_lsp_get_diagnostics():
    with patch("core.mcp.tools.lsp.api_lsp_get_diagnostics") as mock_api:
        mock_api.return_value = {"diagnostics": []}
        res = await lsp_get_diagnostics("test.py")
        assert "diagnostics" in json.loads(res)

        mock_api.side_effect = Exception("failed")
        res = await lsp_get_diagnostics("test.py")
        assert "error" in json.loads(res)
