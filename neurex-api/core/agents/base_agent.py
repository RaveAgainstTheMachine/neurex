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

import json
import os
from abc import ABC, abstractmethod
from collections.abc import AsyncGenerator
from typing import Any

import httpx
import structlog

from api.routes.files import untaint_str
from core.collaboration.manager import collaboration_manager
from core.context.compression import ContextCompressor
from core.context.manager import ContextManager
from core.context.rules_parser import RulesParser
from core.context.skeptical_memory import SkepticalMemory
from core.mcp.client import MCPClient
from core.skills.manager import SkillManager

log = structlog.get_logger()


def get_ollama_base():
    return os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")


def get_default_model():
    return os.getenv("DEFAULT_MODEL", "qwen2.5-coder:14b")


LSP_TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "lsp_go_to_definition",
            "description": "Find the coordinates (file, line, column) and code snippet of a symbol's definition.",
            "parameters": {
                "type": "object",
                "properties": {
                    "file_path": {
                        "type": "string",
                        "description": "Relative path to the file from workspace root",
                    },
                    "line": {"type": "integer", "description": "1-indexed line number"},
                    "col": {"type": "integer", "description": "1-indexed column number"},
                },
                "required": ["file_path", "line", "col"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "lsp_find_references",
            "description": "Find all reference coordinates and line snippets for a symbol in the workspace.",
            "parameters": {
                "type": "object",
                "properties": {
                    "file_path": {
                        "type": "string",
                        "description": "Relative path to the file from workspace root",
                    },
                    "line": {"type": "integer", "description": "1-indexed line number"},
                    "col": {"type": "integer", "description": "1-indexed column number"},
                },
                "required": ["file_path", "line", "col"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "lsp_get_hover",
            "description": "Retrieve semantic information (signature, docstring, type information) under the cursor.",
            "parameters": {
                "type": "object",
                "properties": {
                    "file_path": {
                        "type": "string",
                        "description": "Relative path to the file from workspace root",
                    },
                    "line": {"type": "integer", "description": "1-indexed line number"},
                    "col": {"type": "integer", "description": "1-indexed column number"},
                },
                "required": ["file_path", "line", "col"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "lsp_get_diagnostics",
            "description": "Query compilation errors and warnings currently reported by the language server for a file.",
            "parameters": {
                "type": "object",
                "properties": {
                    "file_path": {
                        "type": "string",
                        "description": "Relative path to the file from workspace root",
                    }
                },
                "required": ["file_path"],
            },
        },
    },
]


class BaseAgent(ABC):
    """All agents inherit from this."""

    system_prompt: str = "You are a helpful AI coding assistant."
    agent_type: str = "base"

    def __init__(
        self,
        rules: RulesParser,
        ctx: ContextManager,
        model: str | None = None,
        autonomy_level: str = "limited",
    ):
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
    async def execute(self, task: dict, conversation_id: str) -> AsyncGenerator[dict, None]:
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
                with open(intel_path) as f:
                    intel = json.load(f)
                    intel_str = json.dumps(intel, indent=2)
                    parts.append(
                        f"\n\n<project_architecture>\n{intel_str}\n</project_architecture>"
                    )
            except Exception:
                pass

        # 3. Scratchpad Injection (Collective Context)
        from core.context.scratchpad import get_scratchpad

        try:
            sp = await get_scratchpad(conversation_id)
            if sp:
                sp_str = json.dumps(sp, indent=2)
                parts.append(f"\n\n<shared_scratchpad>\n{sp_str}\n</shared_scratchpad>")
        except Exception:
            pass

        if extra:
            parts.append(f"\n\n{extra}")
        return "\n".join(parts)

    async def rag_context(self, query: str, n: int = 5) -> str:
        """Retrieve relevant code chunks and past session memories for local recall."""
        # 1. Query past session context from Hive Mind
        from core.memory.hive import hive_mind

        memories = hive_mind.recall(query, limit=3)
        memory_str = ""
        if memories:
            memory_str = (
                "\n\n<session_memory>\n"
                + "\n".join([f"- {m['content']}" for m in memories])
                + "\n</session_memory>"
            )

        # 2. Query code chunks from Federated RAG
        from core.context.federated_rag import FederatedRAG

        frag = FederatedRAG(self.ctx)
        context = await frag.global_search(query, limit=n)

        # 3. Apply Neural Compression
        compressed = await self.compressor.compress_context(context)
        return f"{compressed}{memory_str}"

    async def stream(
        self,
        messages: list[dict],
        model: str | None = None,
        tools: list[dict] | None = None,
        params: str | None = None,
    ) -> AsyncGenerator[dict, None]:
        """Stream from Mesh/Local with high-speed token chunking."""

        # Phase 2.1: Mock LLM for Evals/Baselines
        if os.getenv("NEUREX_MOCK_LLM") == "true":
            # Detect if it's a planning request or an execution request
            if self.agent_type == "planner" or any("exact shape" in m["content"] or "JSON shape" in m["content"] for m in messages if m["role"] == "system"):
                # Planning request
                import re

                # Only look at the current task description part if history is included
                content_parts = messages[-1]["content"].split("Task to execute:")
                target_text = content_parts[-1] if len(content_parts) > 1 else messages[-1]["content"]
                target_text = untaint_str(target_text.lower()[-500:])

                match_text = target_text.split("user request:")[-1] if "user request:" in target_text else target_text
                path_match = re.search(r"([\w\-]+\.(?:py|md|ts|js|jsx|tsx|css|html|json|yaml|yml|toml|sh|txt|rs|go|java|rb|c|cpp|h))\b", match_text)
                if not path_match:
                    if any("hello.py" in msg["content"].lower() for msg in messages):
                        path = "hello.py"
                    else:
                        for msg in reversed(messages):
                            fallback_match = re.search(r"([\w\-]+\.(?:py|md|ts|js|jsx|tsx|css|html|json|yaml|yml|toml|sh|txt|rs|go|java|rb|c|cpp|h))\b", msg["content"])
                            if fallback_match:
                                path_match = fallback_match
                                break
                        path = path_match.group(1) if path_match else "output.txt"
                else:
                    path = path_match.group(1)

                plan = []
                if "named" in target_text and "create hello.py" not in target_text:
                    plan = [
                        {
                            "agent": "coder",
                            "title": "Create workspace structure",
                            "description": "Ensure project folders are ready.",
                        },
                        {
                            "agent": "coder",
                            "title": f"Create {path}",
                            "description": f"Create a file named {path} with appropriate content.",
                        }
                    ]
                else:
                    plan = [
                        {
                            "agent": "coder",
                            "title": f"Create {path}",
                            "description": f"Create a file named {path} with appropriate content.",
                        }
                    ]
                yield {"type": "token", "text": json.dumps(plan)}
                yield {"type": "result", "plan": plan}
                yield {"type": "done", "full_text": json.dumps(plan)}
            else:
                # Execution request
                yield {"type": "token", "text": "Executing task..."}
                
                # Prevent infinite tool execution loop by checking if we already ran a tool call
                has_run_tool = any(m.get("role") == "tool" for m in messages)
                
                if not has_run_tool:
                    # Mock a write_file call if we can guess the path
                    import re

                    # Only look at the current task description to avoid matching files in the history
                    content_parts = messages[-1]["content"].split("Task to execute:")
                    target_text = content_parts[-1] if len(content_parts) > 1 else messages[-1]["content"]
                    target_text = untaint_str(target_text.lower())
                    path_match = re.search(r"([\w\-]+\.(?:py|md|ts|js|jsx|tsx|css|html|json|yaml|yml|toml|sh|txt|rs|go|java|rb|c|cpp|h))", target_text)
                    if path_match:
                        path = path_match.group(1)
                        yield {
                            "type": "tool_call",
                            "call": {
                                "function": {
                                    "name": "write_file",
                                    "arguments": json.dumps(
                                        {
                                            "path": path,
                                            "content": f"# Content for {path}\n# Hello from Mock",
                                        }
                                    ),
                                },
                                "id": "mock_call_1",
                            },
                        }
                yield {"type": "done", "full_text": "Mock execution complete."}
            return

        options = {"temperature": 0.2}
        if params:
            try:
                extra_options = json.loads(params)
                if isinstance(extra_options, dict):
                    options.update(extra_options)
            except json.JSONDecodeError:
                pass

        payload: dict[str, Any] = {
            "model": model or self.model or get_default_model(),
            "messages": messages,
            "stream": True,
            "options": options,
        }

        # Extract top-level API flags (like format) from options
        if "format" in payload["options"]:
            payload["format"] = payload["options"].pop("format")

        if self.agent_type == "planner":
            final_tools = []
        else:
            skill_tools = self.skills.get_enabled_tools()
            # Remove semantic LSP tools because they cause hallucinations for missing languages
            final_tools = (tools or []) + skill_tools
        if final_tools:
            payload["tools"] = final_tools
            
            # Format text tool calling prompt for models that don't support native tool calls
            if "qwen" in payload["model"].lower() or "deepseek" in payload["model"].lower() or "llama" in payload["model"].lower():
                system_instruction = "\n\nYou have access to the following tools:\n"
                for t in final_tools:
                    system_instruction += f"{json.dumps(t['function'])}\n"
                system_instruction += "\nIf you want to say something to the user, you MUST wrap it strictly inside <chat>...</chat> tags. You MUST use this exact JSON format to call a tool OUTSIDE the <chat> tags: {\"name\": \"...\", \"arguments\": {...}}\nCRITICAL: You MUST properly escape all double quotes (\\\") and newlines (\\\\n) inside the JSON string values. Output nothing else after the JSON."
                
                # Append instruction to the first system message
                for i, m in enumerate(messages):
                    if m.get("role") == "system":
                        messages[i] = {**m, "content": m["content"] + system_instruction}
                        break
                        
                # Rewrite role: tool into role: user so these models can see the result
                for i, m in enumerate(messages):
                    if m.get("role") == "tool":
                        messages[i] = {
                            "role": "user",
                            "content": f"Tool execution result:\n{m.get('content')}\n\nContinue with your task based on this result."
                        }

        from core.infrastructure.mesh import mesh_router

        ollama_url = await mesh_router.get_best_inference_node(payload["model"])
        full_text = ""
        previously_yielded_text = ""

        headers = {}
        if "ollama_proxy" in ollama_url:
            peer_url = ollama_url.split("/api/infra")[0]
            if peer_url in mesh_router.peers:
                headers["Authorization"] = f"Bearer {mesh_router.peers[peer_url].token}"

        target_url = (
            f"{ollama_url}/api/chat"
            if "ollama_proxy" not in ollama_url
            else ollama_url.replace("ollama_proxy", "ollama_proxy/api/chat")
        )

        try:
            async with self._client.stream(
                "POST", target_url, json=payload, headers=headers
            ) as resp:
                resp.raise_for_status()
                async for line in resp.aiter_lines():
                    if not line:
                        continue
                    try:
                        data = json.loads(line)
                    except (json.JSONDecodeError, ValueError):
                        continue

                    msg = data.get("message", {})
                    if msg.get("tool_calls"):
                        for tc in msg["tool_calls"]:
                            yield {"type": "tool_call", "call": tc, "full_text": full_text}

                    content = msg.get("content", "")
                    if content:
                        full_text += content
                        import re
                        chat_matches = re.findall(r"<chat>(.*?)</chat>", full_text, flags=re.DOTALL)
                        unclosed_match = re.search(r"<chat>(?!.*</chat>)(.*)$", full_text, flags=re.DOTALL)
                        
                        current_chat_text = "".join(chat_matches)
                        if unclosed_match:
                            unclosed = unclosed_match.group(1)
                            # Prevent partial closing tags from streaming to the UI
                            for i in range(1, 8):
                                if unclosed.endswith("</chat>"[:i]):
                                    unclosed = unclosed[:-i]
                                    break
                            current_chat_text += unclosed
                            
                        new_text = current_chat_text[len(previously_yielded_text):]
                        if new_text:
                            yield {"type": "token", "text": new_text}
                            previously_yielded_text = current_chat_text

                    if data.get("done"):
                        
                        import re
                        is_text_tool_call = False
                        
                        # Find the first JSON-like object that has "name" and "arguments" keys
                        import re
                        pattern = re.compile(r'\{\s*"name"\s*:\s*"[^"]+"\s*,\s*"arguments"\s*:', re.DOTALL)
                        match = pattern.search(full_text)
                        if match:
                            start = match.start()
                            depth = 0
                            for i, ch in enumerate(full_text[start:], start):
                                if ch == '{':
                                    depth += 1
                                elif ch == '}':
                                    depth -= 1
                                    if depth == 0:
                                        potential_json = full_text[start:i+1]
                                        try:
                                            parsed = json.loads(potential_json, strict=False)
                                            if isinstance(parsed, dict) and "name" in parsed and "arguments" in parsed:
                                                tc = {
                                                    "id": f"text_call_{hash(potential_json) & 0xffffffff}",
                                                    "type": "function",
                                                    "function": {
                                                        "name": parsed["name"],
                                                        "arguments": parsed["arguments"]
                                                    }
                                                }
                                                yield {"type": "tool_call", "call": tc, "full_text": full_text[:start].strip()}
                                                is_text_tool_call = True
                                        except Exception:
                                            pass
                                        break
                        
                        if not is_text_tool_call:
                            # Log the raw text to see why it failed or if it was just chat
                            if "{" in full_text and "}" in full_text and ("\"name\"" in full_text or "name:" in full_text):
                                log.warning("stream.json_parse_failed", text=full_text)
                            
                            yield {"type": "done", "full_text": full_text}
        except httpx.HTTPStatusError as e:
            log.error("stream.http_error", status=e.response.status_code, url=target_url)
            yield {"type": "error", "text": f"Inference error: HTTP {e.response.status_code}"}
        except httpx.ConnectError as e:
            log.error("stream.connect_error", url=target_url, error=str(e))
            yield {"type": "error", "text": f"Cannot connect to inference server at {target_url}"}

    async def dispatch_tool(self, tool_call: dict, conversation_id: str) -> str:
        """Route a tool_call with Federated Governance and Neural Linting."""
        from core.observability.flight_recorder import record_decision

        name = tool_call.get("function", {}).get("name", "")
        args = tool_call.get("function", {}).get("arguments", {})
        if isinstance(args, str):
            try:
                args = json.loads(args, strict=False)
            except json.JSONDecodeError:
                args = {}

        mutation_tools = [
            "write_file",
            "delete_file",
            "replace_file_content",
            "multi_replace_file_content",
        ]
        requester = f"agent:{self.agent_type}"
        if name in mutation_tools:
            path = args.get("path") or args.get("TargetFile")

            # Suggest enabling consensus if a file exists and consensus is OFF
            if path:
                try:
                    from core.settings.manager import settings_manager
                    if not settings_manager.get("consensus_enabled"):
                        from core.mcp.tools.filesystem import get_workspace_root
                        ws_root = get_workspace_root()
                        resolved_path = (ws_root / path).resolve()
                        if resolved_path.exists() and resolved_path.is_file():
                            from core.collaboration.presence import presence_manager
                            await presence_manager.broadcast(
                                conversation_id,
                                {
                                    "event": "suggest_consensus",
                                    "data": {
                                        "path": path,
                                        "message": f"Agent is about to modify the existing file '{path}'. Consider enabling Swarm Consensus for additional security."
                                    }
                                }
                            )
                except Exception as e:
                    log.warning("dispatch_tool.suggest_consensus_failed", error=str(e))

            # 1. Collaboration Lock (Phase 44)
            if path and os.getenv("NEUREX_MOCK_LLM") != "true":
                locked = await collaboration_manager.acquire_lock(
                    path, requester, conversation_id=conversation_id
                )
                if not locked:
                    await record_decision(
                        conversation_id=conversation_id,
                        agent_type=self.agent_type,
                        decision=f"block_mutation:{name}",
                        rationale=f"The file '{path}' is currently locked by another entity.",
                    )
                    return f"MUTATION_BLOCKED: The file '{path}' is locked by another entity."

            # 2. Neural Linting (Phase 45: Sentient IDE)
            from core.context.neural_linter import NeuralLinter

            linter = NeuralLinter()
            is_valid, reason = await linter.verify_mutation(name, args, conversation_id)
            if not is_valid:
                log.warning("mutation_lint_failure", file=path, reason=reason)
                await record_decision(
                    conversation_id=conversation_id,
                    agent_type=self.agent_type,
                    decision=f"reject_mutation:{name}",
                    rationale=f"Violation of architectural standards: {reason}",
                )
                return f"MUTATION_REJECTED: Your proposed change violates project architectural standards. Reason: {reason}"

            # 3. Swarm Consensus (Phase 45: Runtime Evolution)
            from core.collaboration.consensus import consensus_manager

            # Skip consensus check if autonomy level is limited or staging (user reviews unified diff at the end)
            is_staged = self.autonomy_level in ("limited", "staging")
            if consensus_manager.is_protected(path) and not is_staged:
                proposal = consensus_manager.get_proposal(path)
                if not proposal:
                    # First attempt to mutate a protected asset
                    res = await consensus_manager.submit_proposal(
                        path, args.get("content") or "", requester
                    )
                    await record_decision(
                        conversation_id=conversation_id,
                        agent_type=self.agent_type,
                        decision=f"propose_mutation:{name}",
                        rationale=f"File '{path}' is protected. Initiating swarm consensus.",
                    )
                    return res

                # If we're here, a proposal exists. Check if consensus reached.
                # Note: The Coder automatically votes YES on submission.
                # Other agents (Reviewer, Planner) will cast votes during their execution loops.
                yes_votes = sum(1 for v in proposal.votes.values() if v)
                if yes_votes < 2:
                    await record_decision(
                        conversation_id=conversation_id,
                        agent_type=self.agent_type,
                        decision=f"wait_consensus:{name}",
                        rationale=f"Waiting for more votes on '{path}'. Current: {yes_votes}/2",
                    )
                    return f"CONSENSUS_REQUIRED: Waiting for swarm agreement on '{path}'. Current votes: {yes_votes}/2"

                # Consensus reached! Clear proposal and allow mutation
                consensus_manager.clear_proposal(path)
                log.info("mutation_approved_by_consensus", file=path)
                await record_decision(
                    conversation_id=conversation_id,
                    agent_type=self.agent_type,
                    decision=f"approve_mutation:{name}",
                    rationale=f"Swarm consensus reached for '{path}'.",
                )

        log.info("tool_dispatch", tool=name, args=args)
        await record_decision(
            conversation_id=conversation_id,
            agent_type=self.agent_type,
            decision=f"dispatch_tool:{name}",
            rationale=f"Executing tool {name} with arguments {json.dumps(args)[:200]}...",
        )
        result = await self.mcp.call(
            name, args, autonomy_level=self.autonomy_level, conversation_id=conversation_id
        )
        return result
