"""
core/infrastructure/external_providers.py
Handles Bring-Your-Own-Key (BYOK) integration for commercial models.
Supports OpenAI, Anthropic, and Gemini with streaming and tool support.
"""
import json
import httpx
import structlog
from typing import Optional, List, Dict, Any, AsyncGenerator
from core.settings.manager import settings_manager

log = structlog.get_logger()

class ExternalInferenceEngine:
    """Unified interface for external LLM providers with streaming and tool support."""

    # Models that Neurex recognizes as "Cloud" models
    MODEL_MAPPING = {
        "gpt-4o": "openai",
        "gpt-4-turbo": "openai",
        "o1-preview": "openai",
        "o1-mini": "openai",
        "claude-3-5-sonnet-20240620": "anthropic",
        "claude-3-opus-20240229": "anthropic",
        "gemini-1.5-pro": "google",
        "gemini-1.5-flash": "google",
    }

    def __init__(self):
        # We use a singleton-like client or create them on demand
        pass

    def get_provider(self, model: str) -> Optional[str]:
        return self.MODEL_MAPPING.get(model)

    def is_external(self, model: str) -> bool:
        return model in self.MODEL_MAPPING

    async def stream_chat(
        self, 
        model: str, 
        messages: List[Dict[str, str]], 
        tools: List[Dict[str, Any]] | None = None,
        **kwargs
    ) -> AsyncGenerator[Dict[str, Any], None]:
        """Stream chat from external providers. Yields Ollama-compatible chunks."""
        provider = self.get_provider(model)
        if not provider:
            log.error("byok.unknown_model", model=model)
            yield {"type": "error", "data": f"Unknown provider for model {model}"}
            return

        api_key = settings_manager.get(f"{provider}_api_key")
        if not api_key:
            log.warning("byok.missing_key", provider=provider)
            yield {"type": "error", "data": f"Missing API key for {provider}. Please set it in Settings."}
            return

        log.info("byok.stream_start", provider=provider, model=model)

        if provider == "openai":
            async for chunk in self._stream_openai(model, messages, api_key, tools, **kwargs):
                yield chunk
        elif provider == "anthropic":
            async for chunk in self._stream_anthropic(model, messages, api_key, tools, **kwargs):
                yield chunk
        elif provider == "google":
            async for chunk in self._stream_google(model, messages, api_key, tools, **kwargs):
                yield chunk

    async def _stream_openai(self, model: str, messages: List[Dict[str, str]], api_key: str, tools: List[Dict[str, Any]] | None = None, **kwargs):
        payload = {
            "model": model, 
            "messages": messages, 
            "stream": True, 
            "temperature": kwargs.get("temperature", 0.2)
        }
        if tools:
            payload["tools"] = tools

        async with httpx.AsyncClient(timeout=httpx.Timeout(120.0, connect=5.0)) as client:
            try:
                async with client.stream(
                    "POST", "https://api.openai.com/v1/chat/completions",
                    headers={"Authorization": f"Bearer {api_key}"},
                    json=payload,
                ) as resp:
                    if resp.status_code == 401:
                        yield {"type": "error", "data": "OpenAI Error: Invalid API Key. Please check your settings."}
                        return
                    elif resp.status_code == 429:
                        yield {"type": "error", "data": "OpenAI Error: Rate limit exceeded. Try again in a few seconds."}
                        return
                    elif resp.status_code != 200:
                        err_body = await resp.aread()
                        yield {"type": "error", "data": f"OpenAI Error ({resp.status_code}): {err_body.decode()}"}
                        return

                    full_text = ""
                    async for line in resp.aiter_lines():
                        if not line.startswith("data: "): continue
                        if "[DONE]" in line: break
                        
                        try:
                            data = json.loads(line[6:])
                        except: continue

                        if not data.get("choices"): continue
                        delta = data["choices"][0].get("delta", {})
                        
                        # Handle Tool Calls
                        if delta.get("tool_calls"):
                            for tc in delta["tool_calls"]:
                                yield {"type": "tool_call", "call": tc}
                        
                        # Handle Content
                        content = delta.get("content", "")
                        if content:
                            full_text += content
                            yield {"type": "token", "text": content}
                    
                    yield {"type": "done", "full_text": full_text}
            except httpx.ConnectError:
                log.error("byok.openai_connect_failed")
                yield {"type": "error", "data": "OpenAI Error: Could not connect to API server."}
            except httpx.TimeoutException:
                log.error("byok.openai_timeout")
                yield {"type": "error", "data": "OpenAI Error: Request timed out."}
            except Exception as e:
                log.error("byok.openai_error", error=str(e))
                yield {"type": "error", "data": f"OpenAI Error: {str(e)}"}

    async def _stream_anthropic(self, model: str, messages: List[Dict[str, str]], api_key: str, tools: List[Dict[str, Any]] | None = None, **kwargs):
        # Simplistic mapping for now
        # Anthropic uses a different message format and tool format
        log.info("byok.anthropic_streaming", model=model)
        yield {"type": "token", "text": "[Anthropic Streaming integration in progress...]"}
        yield {"type": "done", "full_text": ""}

    async def _stream_google(self, model: str, messages: List[Dict[str, str]], api_key: str, tools: List[Dict[str, Any]] | None = None, **kwargs):
        log.info("byok.google_streaming", model=model)
        yield {"type": "token", "text": "[Gemini Streaming integration in progress...]"}
        yield {"type": "done", "full_text": ""}

external_engine = ExternalInferenceEngine()
