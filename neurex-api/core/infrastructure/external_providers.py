"""
core/infrastructure/external_providers.py
Handles Bring-Your-Own-Key (BYOK) integration for commercial models.
Supports OpenAI, Anthropic, and Gemini.
"""
import httpx
import structlog
from typing import Optional, List, Dict, Any
from core.settings.manager import settings_manager

log = structlog.get_logger()

class ExternalInferenceEngine:
    """Unified interface for external LLM providers."""

    def __init__(self):
        self.clients: Dict[str, httpx.AsyncClient] = {
            "openai": httpx.AsyncClient(base_url="https://api.openai.com/v1"),
            "anthropic": httpx.AsyncClient(base_url="https://api.anthropic.com/v1"),
            "google": httpx.AsyncClient(base_url="https://generativelanguage.googleapis.com/v1beta"),
        }

    async def chat_completion(self, provider: str, model: str, messages: List[Dict[str, str]], **kwargs) -> Optional[str]:
        """Generic chat completion for a specific provider."""
        api_key = settings_manager.get(f"{provider}_api_key")
        if not api_key:
            log.warning("byok.missing_key", provider=provider)
            return None

        if provider == "openai":
            return await self._openai_chat(model, messages, api_key, **kwargs)
        elif provider == "anthropic":
            return await self._anthropic_chat(model, messages, api_key, **kwargs)
        elif provider == "google":
            return await self._google_chat(model, messages, api_key, **kwargs)
        
        return None

    async def _openai_chat(self, model: str, messages: List[Dict[str, str]], api_key: str, **kwargs) -> Optional[str]:
        try:
            resp = await self.clients["openai"].post(
                "/chat/completions",
                headers={"Authorization": f"Bearer {api_key}"},
                json={"model": model, "messages": messages, **kwargs},
                timeout=60.0
            )
            resp.raise_for_status()
            return resp.json()["choices"][0]["message"]["content"]
        except Exception as e:
            log.error("byok.openai_error", error=str(e))
            return None

    async def _anthropic_chat(self, model: str, messages: List[Dict[str, str]], api_key: str, **kwargs) -> Optional[str]:
        # Convert messages to Anthropic format if needed
        try:
            resp = await self.clients["anthropic"].post(
                "/messages",
                headers={
                    "x-api-key": api_key,
                    "anthropic-version": "2023-06-01",
                    "content-type": "application/json"
                },
                json={"model": model, "messages": messages, "max_tokens": 4096, **kwargs},
                timeout=60.0
            )
            resp.raise_for_status()
            return resp.json()["content"][0]["text"]
        except Exception as e:
            log.error("byok.anthropic_error", error=str(e))
            return None

    async def _google_chat(self, model: str, messages: List[Dict[str, str]], api_key: str, **kwargs) -> Optional[str]:
        try:
            # Gemini has a different structure
            contents = []
            for m in messages:
                role = "user" if m["role"] == "user" else "model"
                contents.append({"role": role, "parts": [{"text": m["content"]}]})

            resp = await self.clients["google"].post(
                f"/models/{model}:generateContent?key={api_key}",
                json={"contents": contents, **kwargs},
                timeout=60.0
            )
            resp.raise_for_status()
            return resp.json()["candidates"][0]["content"]["parts"][0]["text"]
        except Exception as e:
            log.error("byok.google_error", error=str(e))
            return None

external_engine = ExternalInferenceEngine()
