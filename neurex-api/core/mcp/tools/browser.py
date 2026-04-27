"""
core/mcp/tools/browser.py
Playwright-based browser control tool for agents.
"""
import asyncio
import os
import uuid
from typing import Optional
from playwright.async_api import async_playwright
import structlog

log = structlog.get_logger()

# Global browser instances
_contexts = {}
_playwright = None

async def get_browser(browser_type: str = "chromium"):
    global _contexts, _playwright
    if _playwright is None:
        _playwright = await async_playwright().start()
    
    if browser_type not in _contexts:
        engine = getattr(_playwright, browser_type)
        browser = await engine.launch(headless=True)
        _contexts[browser_type] = await browser.new_context()
        
    return _contexts[browser_type]

async def browser_navigate(url: str, browser_type: str = "chromium") -> str:
    """Navigate to a URL using a specific browser (chromium/firefox/webkit)."""
    context = await get_browser(browser_type)
    page = await context.new_page()
    try:
        await page.goto(url, wait_until="networkidle")
        title = await page.title()
        return f"Navigated to {url}. Title: {title}"
    finally:
        # Keep the page open for subsequent calls if needed, 
        # but for a simple tool we might just return info.
        pass

async def browser_screenshot(browser_type: str = "chromium") -> str:
    """Take a screenshot of the current page and save to artifacts."""
    context = await get_browser(browser_type)
    pages = context.pages
    if not pages:
        return "No pages open."
    
    page = pages[-1]
    filename = f"browser_{uuid.uuid4().hex[:8]}.png"
    ws = os.getenv("WORKSPACE_PATH", "/workspace")
    path = os.path.join(ws, "artifacts", filename)
    
    os.makedirs(os.path.dirname(path), exist_ok=True)
    await page.screenshot(path=path)
    return f"Screenshot saved to artifacts/{filename}"

async def browser_click(selector: str, browser_type: str = "chromium") -> str:
    """Click an element on the current page."""
    context = await get_browser(browser_type)
    if not context.pages: return "No pages open."
    page = context.pages[-1]
    await page.click(selector)
    return f"Clicked {selector}"

async def browser_type(selector: str, text: str, browser_type: str = "chromium") -> str:
    """Type text into an element on the current page."""
    context = await get_browser(browser_type)
    if not context.pages: return "No pages open."
    page = context.pages[-1]
    await page.fill(selector, text)
    return f"Typed into {selector}"

async def browser_get_content(browser_type: str = "chromium") -> str:
    """Return the text content of the current page."""
    context = await get_browser(browser_type)
    if not context.pages: return "No pages open."
    page = context.pages[-1]
    content = await page.content()
    # Simple HTML-to-text placeholder
    return content[:2000] + "..." # Truncated for brevity
