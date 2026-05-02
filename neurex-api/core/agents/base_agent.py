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
import asyncio
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
        # Phase 44.13: Persistent Reasoning Client
        self._client: httpx.AsyncClient = httpx.AsyncClient(timeout=300)

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
            
        # 4. Swarm Collective Intelligence Injection (Phase 49)
        from core.infrastructure.knowledge_base import swarm_kb
        domain = "generic-coding" # Default domain
        lessons = swarm_kb.query_lessons(domain)
        if lessons:
            best_lessons = "\n".join([f"- {l.pattern_id} (Fitness: {l.success_delta})" for l in lessons[:3]])
            parts.append(f"\n\n<global_collective_intelligence>\nDomain: {domain}\nTop Patterns:\n{best_lessons}\n</global_collective_intelligence>")

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
        """Stream from Mesh/Local with high-speed token chunking."""
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
        from core.infrastructure.adapter_orchestrator import adapter_orchestrator

        # Phase 48: Neural Evolution (Specialized Adapter Loading)
        # We determine the domain from the current task context if possible
        domain = "generic-coding" 
        session_id = f"inf-{asyncio.get_event_loop().time()}"
        adapter_id = await adapter_orchestrator.prepare_inference_session(session_id, domain)
        if adapter_id:
            payload["adapter"] = adapter_id

        ollama_url = await mesh_router.get_best_inference_node(payload["model"])
        full_text = ""
        token_buffer = []
        
        headers = {}
        if "ollama_proxy" in ollama_url:
            peer_url = ollama_url.split("/api/infra")[0]
            if peer_url in mesh_router.peers:
                headers["Authorization"] = f"Bearer {mesh_router.peers[peer_url].token}"

        target_url = f"{ollama_url}/api/chat" if "ollama_proxy" not in ollama_url else ollama_url.replace("ollama_proxy", "ollama_proxy/api/chat")

        try:
            async with self._client.stream("POST", target_url, json=payload, headers=headers) as resp:
                resp.raise_for_status()
                async for line in resp.aiter_lines():
                    if not line: continue
                    try:
                        import json
                        data = json.loads(line)
                    except: continue
                    
                    msg = data.get("message", {})
                    if msg.get("tool_calls"):
                        # Flush token buffer before tool call
                        if token_buffer:
                            yield {"type": "token", "text": "".join(token_buffer)}
                            token_buffer = []
                        for tc in msg["tool_calls"]: yield {"type": "tool_call", "call": tc}
                    
                    content = msg.get("content", "")
                    if content:
                        full_text += content
                        token_buffer.append(content)
                        # Yield in chunks of 10 tokens to reduce WS pressure
                        if len(token_buffer) >= 10:
                            yield {"type": "token", "text": "".join(token_buffer)}
                            token_buffer = []
                    
                    if data.get("done"):
                        # Flush remaining tokens
                        if token_buffer:
                            yield {"type": "token", "text": "".join(token_buffer)}
                        yield {"type": "done", "full_text": full_text}
        finally:
            adapter_orchestrator.release_session(session_id)

    async def dispatch_tool(self, tool_call: dict, conversation_id: str) -> str:
        """Route a tool_call with Federated Governance and Neural Linting."""
        name = tool_call.get("function", {}).get("name", "")
        args = tool_call.get("function", {}).get("arguments", {})
        
        mutation_tools = ["write_file", "delete_file", "replace_file_content", "multi_replace_file_content"]
        if name in mutation_tools:
            path = args.get("path") or args.get("TargetFile")
            
            # 1. Collaboration Lock (Phase 44)
            if path:
                requester = f"agent:{self.agent_type}"
                locked = await collaboration_manager.acquire_lock(path, requester, conversation_id=conversation_id)
                if not locked:
                    return f"MUTATION_BLOCKED: The file '{path}' is locked by another entity."

            # 2. Neural Linting (Phase 45: Sentient IDE)
            from core.context.neural_linter import NeuralLinter
            linter = NeuralLinter()
            is_valid, reason = await linter.verify_mutation(name, args, conversation_id)
            if not is_valid:
                log.warning("mutation_lint_failure", file=path, reason=reason)
                return f"MUTATION_REJECTED: Your proposed change violates project architectural standards. Reason: {reason}"

            # 3. Swarm Consensus (Phase 45: Runtime Evolution)
            from core.collaboration.consensus import consensus_manager
            if consensus_manager.is_protected(path):
                proposal = consensus_manager.get_proposal(path)
                if not proposal:
                    # First attempt to mutate a protected asset
                    res = await consensus_manager.submit_proposal(path, args.get("content") or "", requester)
                    return res
                
                # If we're here, a proposal exists. Check if consensus reached.
                # Note: The Coder automatically votes YES on submission.
                # Other agents (Reviewer, Planner) will cast votes during their execution loops.
                yes_votes = sum(1 for v in proposal.votes.values() if v)
                if yes_votes < 3:
                    return f"CONSENSUS_REQUIRED: Waiting for swarm agreement on '{path}'. Current votes: {yes_votes}/3"
                
                # Consensus reached! Clear proposal and allow mutation
                consensus_manager.clear_proposal(path)
                log.info("mutation_approved_by_consensus", file=path)

        log.info("tool_dispatch", tool=name, args=args)
        result = await self.mcp.call(name, args, autonomy_level=self.autonomy_level, conversation_id=conversation_id)
        
        # Phase 45: Zero-Restart Runtime Evolution
        if name in mutation_tools and ".py" in str(args.get("path") or args.get("TargetFile")):
            from core.infrastructure.live_reloader import live_reloader
            path = args.get("path") or args.get("TargetFile")
            if path:
                reloaded = live_reloader.reload_module(path)
                if reloaded:
                    log.info("runtime.module_evolved", file=path)
        
        return result
