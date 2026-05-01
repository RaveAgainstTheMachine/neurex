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
from core.skills.manager import SkillManager
from core.collaboration.manager import collaboration_manager
from core.context.compression import ContextCompressor

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

    # ── Subclasses implement these ────────────────────────────────────────

    @abstractmethod
    async def execute(
        self, task: dict, conversation_id: str
    ) -> AsyncGenerator[dict, None]:
        """Execute a task step and yield structured chunks."""
        ...

    # ── Shared helpers ────────────────────────────────────────────────────

    async def build_system_prompt(self, conversation_id: str, extra: str = "") -> str:
        rules = self.rules.get_merged_rules()
        parts = [self.system_prompt]
        
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
            
        parts.append("\n- SCRATCHPAD RULE: Use `set_scratchpad` to store critical findings (e.g. library bugs, architectural notes) for your sibling agents. Check the `<shared_scratchpad>` block for notes left by others.")

        if extra:
            parts.append(f"\n\n{extra}")
        return "\n".join(parts)

    async def rag_context(self, query: str, n: int = 5) -> str:
        """Retrieve relevant code chunks via Neural RAG 2.0 (Hybrid Search)."""
        # Phase 25: Using NeuralExplorer for AST-aware hybrid retrieval
        chunks = await self.ctx.explorer.hybrid_search(query, limit=n)
        if not chunks:
            return ""
        formatted = "\n\n".join(
            f"# {c['metadata'].get('file', 'unknown')} (line {c['metadata'].get('start_line', '?')})\n{c['document']}"
            for c in chunks
        )
        # Apply Neural Compression (Phase 22)
        compressed = await self.compressor.compress_context(formatted)
        return f"<codebase_context>\n{compressed}\n</codebase_context>"

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

        # Merge dynamic skills
        skill_tools = self.skills.get_enabled_tools()
        final_tools = (tools or []) + skill_tools

        if final_tools:
            payload["tools"] = final_tools

        from core.infrastructure.mesh import mesh_router

        # 2. Otherwise, route to local Mesh (Ollama)
        ollama_url = await mesh_router.get_best_inference_node(payload["model"])
        full_text = ""
        # Increase timeout for complex mesh generation
        async with httpx.AsyncClient(timeout=300) as client:
            # We may be routing to a peer, so we need to add the peer's token if applicable
            headers = {}
            if "ollama_proxy" in ollama_url:
                peer_url = ollama_url.split("/api/infra")[0]
                if peer_url in mesh_router.peers:
                    headers["Authorization"] = f"Bearer {mesh_router.peers[peer_url].token}"

            target_url = f"{ollama_url}/api/chat" if "ollama_proxy" not in ollama_url else ollama_url.replace("ollama_proxy", "ollama_proxy/api/chat")

            async with client.stream(
                "POST",
                target_url,
                json=payload,
                headers=headers
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

    async def record_decision(self, conversation_id: str, decision: str, rationale: str, task_id: str | None = None):
        """Helper to log an agentic decision to the flight recorder."""
        from core.observability.flight_recorder import record_decision
        await record_decision(conversation_id, self.agent_type, decision, rationale, task_id=task_id)

    async def dispatch_tool(self, tool_call: dict, conversation_id: str) -> str:
        """Route a tool_call from the model to the MCP client with Federated Governance."""
        name = tool_call.get("function", {}).get("name", "")
        args = tool_call.get("function", {}).get("arguments", {})
        
        # 1. Federated Governance: Mutation Locking
        mutation_tools = ["write_file", "delete_file", "replace_file_content", "multi_replace_file_content"]
        if name in mutation_tools:
            path = args.get("path") or args.get("TargetFile")
            if path:
                # Try to auto-acquire lock for the agent
                requester = f"agent:{self.agent_type}"
                locked = await collaboration_manager.acquire_lock(path, requester, conversation_id=conversation_id)
                if not locked:
                    msg = f"MUTATION_BLOCKED: The file '{path}' is currently locked by another entity. Wait or choose another task."
                    log.warn("collaboration.dispatch_blocked", tool=name, path=path, requester=requester)
                    return msg

        log.info("tool_dispatch", tool=name, args=args, autonomy=self.autonomy_level)
        return await self.mcp.call(name, args, autonomy_level=self.autonomy_level, conversation_id=conversation_id)
