"""
core/agents/base_agent.py
Abstract base for all Neurex agents. Handles:
  - Prompt assembly (system prompt + rules + RAG context + history)
  - Ollama streaming
  - Tool dispatch via MCP client
  - Token budget enforcement
"""
from __future__ import annotations
import os
from abc import ABC, abstractmethod
from typing import AsyncGenerator, Any

import httpx
import structlog

from core.context.manager import ContextManager
from core.context.rules_parser import RulesParser
from core.mcp.client import MCPClient

log = structlog.get_logger()

def get_ollama_base():
    return os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")

def get_default_model():
    return os.getenv("DEFAULT_MODEL", "qwen2.5-coder:14b")



class BaseAgent(ABC):
    """All agents inherit from this."""

    system_prompt: str = "You are a helpful AI coding assistant."
    agent_type: str = "base"

    def __init__(self, rules: RulesParser, ctx: ContextManager, model: str | None = None):
        self.rules = rules
        self.ctx = ctx
        self.mcp = MCPClient()
        self.model = model

    # ── Subclasses implement these ────────────────────────────────────────

    @abstractmethod
    async def execute(
        self, task: dict, conversation_id: str
    ) -> AsyncGenerator[dict, None]:
        """Execute a task step and yield structured chunks."""
        ...

    # ── Shared helpers ────────────────────────────────────────────────────

    def build_system_prompt(self, extra: str = "") -> str:
        rules = self.rules.get_merged_rules()
        parts = [self.system_prompt]
        if rules:
            parts.append(f"\n\n<rules>\n{rules}\n</rules>")
        if extra:
            parts.append(f"\n\n{extra}")
        return "\n".join(parts)

    async def rag_context(self, query: str, n: int = 5) -> str:
        """Retrieve relevant code chunks from ChromaDB."""
        chunks = await self.ctx.retrieve(query, n_results=n)
        if not chunks:
            return ""
        formatted = "\n\n".join(
            f"# {c['metadata'].get('file', 'unknown')} (line {c['metadata'].get('start_line', '?')})\n{c['document']}"
            for c in chunks
        )
        return f"<codebase_context>\n{formatted}\n</codebase_context>"

    async def stream(
        self,
        messages: list[dict],
        model: str | None = None,
        tools: list[dict] | None = None,
    ) -> AsyncGenerator[dict, None]:
        """
        Stream from Ollama and yield:
          {"type": "token",     "text": "..."}
          {"type": "tool_call", "call": {...}}
          {"type": "done",      "full_text": "..."}
        """
        payload: dict[str, Any] = {
            "model": model or self.model or get_default_model(),
            "messages": messages,
            "stream": True,
            "options": {"temperature": 0.2, "num_gpu": 99},

        }

        if tools:
            payload["tools"] = tools

        full_text = ""
        async with httpx.AsyncClient(timeout=300) as client:
            async with client.stream(
                "POST",
                f"{get_ollama_base()}/api/chat",

                json=payload,
            ) as resp:
                resp.raise_for_status()
                async for line in resp.aiter_lines():
                    if not line:
                        continue
                    log.debug("ollama.stream_line", line=line[:100])

                    try:
                        import json
                        data = json.loads(line)
                    except Exception:
                        continue

                    msg = data.get("message", {})

                    # Tool call
                    if msg.get("tool_calls"):
                        for tc in msg["tool_calls"]:
                            yield {"type": "tool_call", "call": tc}

                    # Text token
                    content = msg.get("content", "")
                    if content:
                        full_text += content
                        yield {"type": "token", "text": content}

                    if data.get("done"):
                        yield {"type": "done", "full_text": full_text}

    async def dispatch_tool(self, tool_call: dict) -> str:
        """Route a tool_call from the model to the MCP client."""
        name = tool_call.get("function", {}).get("name", "")
        args = tool_call.get("function", {}).get("arguments", {})
        log.info("tool_dispatch", tool=name, args=args)
        return await self.mcp.call(name, args)
