"""
core/agents/base_agent.py
Abstract base for all Neurex agents. Handles:
  - Prompt assembly (system prompt + rules + RAG context + history)
  - Ollama streaming
  - Tool dispatch via MCP client
  - Token budget enforcement
  - Skeptical Memory (Phase 31)
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
from core.skills.manager import SkillManager
from core.collaboration.manager import collaboration_manager
from core.context.compression import ContextCompressor
from core.context.skeptical_memory import SkepticalMemory

log = structlog.get_logger()

def get_ollama_base():
    return os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")

def get_default_model():
    return os.getenv("DEFAULT_MODEL", "qwen2.5-coder:14b")

class BaseAgent(ABC):
    """All agents inherit from this."""

    system_prompt: str = "You are a helpful AI coding assistant."
    agent_type: str = "base"

    def __init__(self, rules: RulesParser, ctx: ContextManager, model: str | None = None, autonomy_level: str = "limited"):
        self.rules = rules
        self.ctx = ctx
        self.mcp = MCPClient()
        self.skills = SkillManager()
        self.model = model
        self.autonomy_level = autonomy_level
        self.compressor = ContextCompressor(ctx)
        self.skeptical_memory = SkepticalMemory(os.getenv("WORKSPACE_PATH", os.getcwd()))

    @abstractmethod
    async def execute(
        self, task: dict, conversation_id: str
    ) -> AsyncGenerator[dict, None]:
        """Execute a task step and yield structured chunks."""
        ...

    async def build_system_prompt(self, conversation_id: str, extra: str = "") -> str:
        parts = [self.system_prompt]
        
        # Phase 31: Skeptical Memory Directive
        parts.append(self.skeptical_memory.get_skeptical_instruction())
        
        # 1. Project Intelligence Injection
        ws = os.getenv("WORKSPACE_PATH", "/workspace")
        intel_path = os.path.join(ws, ".neurex", "intel.json")
        if os.path.exists(intel_path):
            try:
                import json
                with open(intel_path, "r") as f:
                    intel = json.load(f)
                    intel_str = json.dumps(intel, indent=2)
                    parts.append(f"\n\n<project_architecture>\n{intel_str}\n</project_architecture>")
            except Exception:
                pass

        # 3. Scratchpad Injection (Collective Context)
        from core.context.scratchpad import get_scratchpad
        try:
            sp = await get_scratchpad(conversation_id)
            if sp:
                import json
                sp_str = json.dumps(sp, indent=2)
                parts.append(f"\n\n<shared_scratchpad>\n{sp_str}\n</shared_scratchpad>")
        except Exception:
            pass
            
        parts.append("\n- SCRATCHPAD RULE: Use `set_scratchpad` to store critical findings for sibling agents.")

        if extra:
            parts.append(f"\n\n{extra}")
        return "\n".join(parts)

    async def rag_context(self, query: str, n: int = 5) -> str:
        """Retrieve relevant code chunks via Mesh-Scale Distributed RAG (Global Intelligence)."""
        # Phase 37: Federated RAG across the Mesh
        from core.context.federated_rag import FederatedRAG
        frag = FederatedRAG(self.ctx)
        
        # Perform global search (Local + Peer Nodes)
        context = await frag.global_search(query, limit=n)
        
        # Apply Neural Compression (Phase 22)
        compressed = await self.compressor.compress_context(context)
        return compressed

    async def stream(
        self,
        messages: list[dict],
        model: str | None = None,
        tools: list[dict] | None = None,
    ) -> AsyncGenerator[dict, None]:
        """Stream from Mesh/Local and yield tokens/tool_calls."""
        payload: dict[str, Any] = {
            "model": model or self.model or get_default_model(),
            "messages": messages,
            "stream": True,
            "options": {"temperature": 0.2},
        }

        skill_tools = self.skills.get_enabled_tools()
        final_tools = (tools or []) + skill_tools
        if final_tools:
            payload["tools"] = final_tools

        from core.infrastructure.mesh import mesh_router
        ollama_url = await mesh_router.get_best_inference_node(payload["model"])
        full_text = ""
        
        async with httpx.AsyncClient(timeout=300) as client:
            headers = {}
            if "ollama_proxy" in ollama_url:
                peer_url = ollama_url.split("/api/infra")[0]
                if peer_url in mesh_router.peers:
                    headers["Authorization"] = f"Bearer {mesh_router.peers[peer_url].token}"

            target_url = f"{ollama_url}/api/chat" if "ollama_proxy" not in ollama_url else ollama_url.replace("ollama_proxy", "ollama_proxy/api/chat")

            async with client.stream("POST", target_url, json=payload, headers=headers) as resp:
                resp.raise_for_status()
                async for line in resp.aiter_lines():
                    if not line: continue
                    try:
                        import json
                        data = json.loads(line)
                    except: continue
                    msg = data.get("message", {})
                    if msg.get("tool_calls"):
                        for tc in msg["tool_calls"]: yield {"type": "tool_call", "call": tc}
                    content = msg.get("content", "")
                    if content:
                        full_text += content
                        yield {"type": "token", "text": content}
                    if data.get("done"):
                        yield {"type": "done", "full_text": full_text}

    async def dispatch_tool(self, tool_call: dict, conversation_id: str) -> str:
        """Route a tool_call with Federated Governance."""
        name = tool_call.get("function", {}).get("name", "")
        args = tool_call.get("function", {}).get("arguments", {})
        
        mutation_tools = ["write_file", "delete_file", "replace_file_content", "multi_replace_file_content"]
        if name in mutation_tools:
            path = args.get("path") or args.get("TargetFile")
            if path:
                requester = f"agent:{self.agent_type}"
                locked = await collaboration_manager.acquire_lock(path, requester, conversation_id=conversation_id)
                if not locked:
                    return f"MUTATION_BLOCKED: The file '{path}' is locked by another entity."

        log.info("tool_dispatch", tool=name, args=args)
        return await self.mcp.call(name, args, autonomy_level=self.autonomy_level, conversation_id=conversation_id)
