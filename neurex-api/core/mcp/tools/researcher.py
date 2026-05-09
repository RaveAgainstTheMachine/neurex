"""
core/mcp/tools/researcher.py
Web research tools for the Neurex Researcher agent.
Uses DuckDuckGo to search for documentation and technical solutions.
"""
from __future__ import annotations

import asyncio

import structlog
from duckduckgo_search import DDGS

log = structlog.get_logger()

async def web_search(query: str, max_results: int = 5) -> str:
    """
    Search the web for technical documentation or code examples.
    """
    log.info("mcp.web_search.start", query=query, max_results=max_results)
    
    try:
        # DDGS is synchronous; offload to thread to avoid blocking the event loop
        def sync_search():
            with DDGS() as ddgs:
                return list(ddgs.text(query, max_results=max_results))

        results = await asyncio.to_thread(sync_search)
            
        if not results:
            log.info("mcp.web_search.no_results", query=query)
            return f"No results found for '{query}'."
            
        formatted = []
        for r in results:
            formatted.append(f"Title: {r['title']}\nURL: {r['href']}\nSnippet: {r['body']}\n")
            
        summary = "\n---\n".join(formatted)
        log.info("mcp.web_search.done", query=query, result_count=len(results))
        return summary
        
    except Exception as e:
        log.error("mcp.web_search.error", query=query, error=str(e))
        return f"Error during web search: {str(e)}"
