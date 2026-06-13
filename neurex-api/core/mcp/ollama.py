import json
from collections.abc import AsyncGenerator
from typing import Any

import httpx
import structlog

from ..settings.manager import settings_manager

log = structlog.get_logger()


class OllamaManager:
    def __init__(self):
        self.base_url = settings_manager.get("ollama_base_url") or "http://localhost:11434"
        self.client = httpx.AsyncClient(
            base_url=self.base_url,
            timeout=httpx.Timeout(60.0, connect=5.0),
            limits=httpx.Limits(max_keepalive_connections=5, max_connections=10),
        )
        self.vram = None  # Infrastructure metrics handled globally

    async def get_running_models(self) -> list[dict[str, Any]]:
        try:
            r = await self.client.get("/api/ps")
            r.raise_for_status()
            return r.json().get("models", [])
        except (httpx.ConnectError, httpx.TimeoutException) as e:
            log.warning("ollama.service_unreachable", error=str(e), endpoint="/api/ps")
            return []
        except Exception as e:
            log.error("ollama.ps_failed", error=str(e))
            return []

    async def get_tags(self) -> list[dict[str, Any]]:
        try:
            r = await self.client.get("/api/tags")
            r.raise_for_status()
            return r.json().get("models", [])
        except (httpx.ConnectError, httpx.TimeoutException) as e:
            log.warning("ollama.service_unreachable", error=str(e), endpoint="/api/tags")
            return []
        except Exception as e:
            log.error("ollama.tags_failed", error=str(e))
            return []

    async def pull_model(self, name: str):
        log.info("ollama.pull_start", model=name)
        try:
            async with self.client.stream("POST", "/api/pull", json={"name": name}) as r:
                r.raise_for_status()
                async for line in r.aiter_lines():
                    if line:
                        try:
                            data = json.loads(line)
                            # Progress reporting could go here
                        except json.JSONDecodeError:
                            continue
        except Exception as e:
            log.error("ollama.pull_failed", model=name, error=str(e))
            raise
        log.info("ollama.pull_done", model=name)

    async def generate(
        self, model: str, prompt: str, system: str | None = None, stream: bool = False
    ):
        payload = {"model": model, "prompt": prompt, "stream": stream}
        if system:
            payload["system"] = system

        try:
            if stream:
                return self._stream_generate(payload)
            else:
                r = await self.client.post("/api/generate", json=payload)
                r.raise_for_status()
                return r.json()
        except (httpx.ConnectError, httpx.TimeoutException) as e:
            log.error("ollama.generate_unreachable", error=str(e), model=model)
            raise RuntimeError(f"Ollama service is unreachable: {e}")
        except Exception as e:
            log.error("ollama.generate_failed", error=str(e), model=model)
            raise

    async def _stream_generate(
        self, payload: dict[str, Any]
    ) -> AsyncGenerator[dict[str, Any], None]:
        try:
            async with self.client.stream("POST", "/api/generate", json=payload) as r:
                r.raise_for_status()
                async for line in r.aiter_lines():
                    if line:
                        try:
                            yield json.loads(line)
                        except json.JSONDecodeError:
                            continue
        except Exception as e:
            log.error("ollama.stream_generate_failed", error=str(e))
            yield {"error": str(e)}

    async def chat(self, model: str, messages: list[dict[str, str]], stream: bool = False):
        payload = {"model": model, "messages": messages, "stream": stream}
        try:
            if stream:
                return self._stream_chat(payload)
            else:
                r = await self.client.post("/api/chat", json=payload)
                r.raise_for_status()
                return r.json()
        except (httpx.ConnectError, httpx.TimeoutException) as e:
            log.error("ollama.chat_unreachable", error=str(e), model=model)
            raise RuntimeError(f"Ollama service is unreachable: {e}")
        except Exception as e:
            log.error("ollama.chat_failed", error=str(e), model=model)
            raise

    async def _stream_chat(self, payload: dict[str, Any]) -> AsyncGenerator[dict[str, Any], None]:
        try:
            async with self.client.stream("POST", "/api/chat", json=payload) as r:
                r.raise_for_status()
                async for line in r.aiter_lines():
                    if line:
                        try:
                            yield json.loads(line)
                        except json.JSONDecodeError:
                            continue
        except Exception as e:
            log.error("ollama.stream_chat_failed", error=str(e))
            yield {"error": str(e)}

    async def ensure_model(self, name: str):
        try:
            tags = await self.get_tags()
            if not any(t["name"] == name for t in tags):
                await self.pull_model(name)
        except Exception as e:
            log.error("ollama.ensure_model_failed", model=name, error=str(e))

    async def stop_all_models(self):
        try:
            running = await self.get_running_models()
            for m in running:
                await self.client.post("/api/generate", json={"model": m["name"], "keep_alive": 0})
        except Exception as e:
            log.error("ollama.stop_all_failed", error=str(e))

    async def preload_model(self, name: str):
        try:
            await self.client.post(
                "/api/generate", json={"model": name, "prompt": "", "keep_alive": -1}
            )
        except Exception as e:
            log.error("ollama.preload_failed", model=name, error=str(e))

    async def unload_model(self, name: str):
        try:
            await self.client.post("/api/generate", json={"model": name, "keep_alive": 0})
        except Exception as e:
            log.error("ollama.unload_failed", model=name, error=str(e))

    async def get_metrics(self) -> dict[str, Any]:
        try:
            from core.infrastructure.manager import infrastructure_manager

            return infrastructure_manager.get_system_metrics()
        except Exception as e:
            log.error("ollama.metrics_failed", error=str(e))
            return {}


# Singleton
ollama_manager = OllamaManager()
