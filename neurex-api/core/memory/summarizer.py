"""
core/memory/summarizer.py
Lightweight summarization service for semantic enrichment of codebase indexing.
"""
import httpx
import os
import structlog

log = structlog.get_logger()

OLLAMA_BASE = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
SUMMARIZER_MODEL = os.getenv("SUMMARIZER_MODEL", "qwen2.5-coder:1.5b")

class Summarizer:
    def __init__(self):
        self.client = httpx.AsyncClient(timeout=30.0)

    async def summarize_chunk(self, content: str) -> str:
        """Generate a one-sentence technical summary of a code chunk."""
        prompt = (
            "Summarize this code chunk in exactly one sentence of technical prose. "
            "Focus on the 'what' and 'why'. No conversational filler.\n\n"
            f"Code:\n{content[:2000]}"
        )
        try:
            resp = await self.client.post(
                f"{OLLAMA_BASE}/api/generate",
                json={
                    "model": SUMMARIZER_MODEL,
                    "prompt": prompt,
                    "stream": False,
                    "options": {"num_predict": 100, "temperature": 0.1}
                }
            )
            if resp.status_code == 200:
                summary = resp.json().get("response", "").strip()
                return summary
            return ""
        except Exception as e:
            log.debug("summarizer.failed", error=str(e))
            return ""

    async def close(self):
        await self.client.aclose()
