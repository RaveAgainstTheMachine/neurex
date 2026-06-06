"""
core/agents/summarizer_agent.py
Last-resort context compression. Called by ContextManager when the
conversation history still exceeds budget after sliding-window trimming.

Strategy:
  - Feed the oldest N messages to the model with a compression prompt
  - Replace those messages with a single summary message
  - Preserve any tool call/result pairs intact (they're semantically dense)

This is intentionally a fallback — the primary strategy is KV-cache pinning
+ sliding window (see core/context/manager.py).
"""

from __future__ import annotations

import structlog

from core.agents.base_agent import BaseAgent
from core.context.manager import ContextManager
from core.context.rules_parser import RulesParser

log = structlog.get_logger()

SUMMARIZER_SYSTEM = """\
You are a context compression assistant. You will receive a sequence of chat
messages from an AI coding session. Your job is to write a concise summary
(maximum 300 words) that preserves:
  - Which files were created or modified, and the key decisions made
  - Any errors encountered and how they were resolved
  - Outstanding tasks that were not yet completed
  - Important constraints or rules that were established

Output ONLY the summary text. No preamble, no markdown.
"""


class SummarizerAgent(BaseAgent):
    system_prompt = SUMMARIZER_SYSTEM
    agent_type = "summarizer"

    def __init__(self, rules: RulesParser, ctx: ContextManager):
        super().__init__(rules, ctx)

    async def summarize(self, messages: list[dict]) -> str:
        """
        Summarize a list of messages into a compact string.
        Returns the summary text (blocking, not streaming).
        """
        # Format messages for summarization
        formatted = []
        for m in messages:
            role = m.get("role", "unknown")
            content = m.get("content") or ""
            if not content:
                # Tool call with no text content
                tool_calls = m.get("tool_calls", [])
                if tool_calls:
                    content = f"[Tool call: {', '.join(tc.get('function', {}).get('name', '?') for tc in tool_calls)}]"
            if content:
                formatted.append(f"{role.upper()}: {content[:500]}")

        if not formatted:
            return ""

        transcript = "\n\n".join(formatted)

        summary_messages = [
            {"role": "system", "content": SUMMARIZER_SYSTEM},
            {"role": "user", "content": f"Summarize this session:\n\n{transcript}"},
        ]

        full_text = ""
        async for chunk in self.stream(summary_messages):
            if chunk["type"] == "token":
                full_text += chunk["text"]
            elif chunk["type"] == "done":
                break

        log.info("summarizer.done", original_messages=len(messages), summary_chars=len(full_text))
        return full_text.strip()

    async def execute(self, task: dict, conversation_id: str):
        # Satisfy ABC — SummarizerAgent is invoked via summarize(), not execute()
        summary = await self.summarize([{"role": "user", "content": task.get("description", "")}])
        yield {"type": "result", "result": summary}

    def compress_history(
        self,
        messages: list[dict],
        keep_last: int = 6,
    ) -> tuple[list[dict], list[dict]]:
        """
        Split messages into (to_summarize, to_keep).
        Keeps system messages and the last `keep_last` exchanges intact.
        """
        system = [m for m in messages if m.get("role") == "system"]
        non_sys = [m for m in messages if m.get("role") != "system"]

        if len(non_sys) <= keep_last:
            return [], messages

        to_summarize = non_sys[:-keep_last]
        to_keep = non_sys[-keep_last:]

        return to_summarize, system + to_keep
