from unittest.mock import AsyncMock, patch

import pytest

from core.mcp.tools.browser import (
    browser_click,
    browser_get_content,
    browser_navigate,
    browser_screenshot,
    browser_type,
)


@pytest.fixture(autouse=True)
def reset_browser_state():
    # Reset globals before each test
    import core.mcp.tools.browser as browser_module
    browser_module._contexts = {}
    browser_module._playwright = None
    yield
    browser_module._contexts = {}
    browser_module._playwright = None

@pytest.fixture
def mock_playwright():
    mock_pw = AsyncMock()
    mock_browser = AsyncMock()
    mock_context = AsyncMock()
    
    mock_pw.chromium.launch.return_value = mock_browser
    mock_browser.new_context.return_value = mock_context
    
    mock_page = AsyncMock()
    mock_context.new_page.return_value = mock_page
    mock_context.pages = [mock_page]
    
    mock_pw_context_mgr = AsyncMock()
    mock_pw_context_mgr.start.return_value = mock_pw
    
    with patch("core.mcp.tools.browser.async_playwright", return_value=mock_pw_context_mgr):
        yield mock_context, mock_page

@pytest.mark.asyncio
async def test_browser_navigate(mock_playwright):
    context, page = mock_playwright
    page.title.return_value = "Test Title"
    
    res = await browser_navigate("https://example.com")
    assert "Navigated to" in res
    assert "Test Title" in res
    page.goto.assert_called_once_with("https://example.com", wait_until="networkidle")

@pytest.mark.asyncio
async def test_browser_screenshot(mock_playwright, tmp_path, monkeypatch):
    monkeypatch.setenv("WORKSPACE_PATH", str(tmp_path))
    context, page = mock_playwright
    
    res = await browser_screenshot()
    assert "Screenshot saved" in res
    page.screenshot.assert_called_once()
    
    # Test no pages
    context.pages = []
    res2 = await browser_screenshot()
    assert res2 == "No pages open."

@pytest.mark.asyncio
async def test_browser_click(mock_playwright):
    context, page = mock_playwright
    res = await browser_click("#btn")
    assert "Clicked #btn" in res
    page.click.assert_called_once_with("#btn")

@pytest.mark.asyncio
async def test_browser_type(mock_playwright):
    context, page = mock_playwright
    res = await browser_type("#input", "hello")
    assert "Typed into" in res
    page.fill.assert_called_once_with("#input", "hello")

@pytest.mark.asyncio
async def test_browser_get_content(mock_playwright):
    context, page = mock_playwright
    page.inner_text.return_value = "hello world"
    
    res = await browser_get_content()
    assert res == "hello world"
    page.inner_text.assert_called_once_with("body")
    
    page.inner_text.return_value = "a" * 20000
    res2 = await browser_get_content()
    assert len(res2) == 10000 + len("\n... [truncated]")
    
    page.inner_text.side_effect = Exception("failed")
    res3 = await browser_get_content()
    assert "Could not extract" in res3
