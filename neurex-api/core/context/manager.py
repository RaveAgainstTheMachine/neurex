"""
core/context/manager.py
Dynamic context manager. Handles RAG retrieval and token budgets.
Updated to support local PersistentClient for non-docker environments.
"""
from __future__ import annotations
import os
import httpx
import structlog
import tiktoken
import chromadb
from core.memory.embedder import Embedder, Reranker

log = structlog.get_logger()

CHROMA_DB_DIR  = os.getenv("CHROMA_DB_DIR", "/games/AI/chroma_db")
COLLECTION     = "neurex_codebase"

CONTEXT_WINDOW   = 8192
SYSTEM_BUDGET    = 1500
RAG_BUDGET       = 2000
TOOL_OUTPUT_MAX  = 1000
HISTORY_BUDGET   = CONTEXT_WINDOW - SYSTEM_BUDGET - RAG_BUDGET - 512

class ContextManager:
    def __init__(self):
        self.embedder = Embedder()
        self.reranker = Reranker()
        self._enc = tiktoken.get_encoding("cl100k_base")
        self._chroma = None
        self._collection = None

    def _get_collection(self):
        """Synchronous retrieval of collection from PersistentClient."""
        if self._chroma is None:
            # Use PersistentClient for local execution
            self._chroma = chromadb.PersistentClient(path=CHROMA_DB_DIR)
            self._collection = self._chroma.get_or_create_collection(COLLECTION)
        return self._collection

    async def retrieve(self, query: str, n_results: int = 20) -> list[dict]:
        """Embed → ANN search → rerank → return top-k within budget."""
        try:
            # PersistentClient operations are sync, offload to thread
            def query_sync():
                collection = self._get_collection()
                return collection.query(
                    query_embeddings=[embedding],
                    n_results=min(n_results, 20),
                    include=["documents", "metadatas", "distances"],
                )

            embedding = await self.embedder.embed(query)
            results = await asyncio.to_thread(query_sync)
            
            candidates = [
                {"document": doc, "metadata": meta, "distance": dist}
                for doc, meta, dist in zip(
                    results["documents"][0],
                    results["metadatas"][0],
                    results["distances"][0],
                )
            ]

            reranked = self.reranker.rerank(query, candidates, top_k=10)
            return self._budget_chunks(reranked, RAG_BUDGET)
            
        except Exception as e:
            log.error("context.retrieve_error", error=str(e))
            return []

    # ... [Rest of the methods remain same, but I'll provide full file as per rules]
    
    def trim_history(self, messages: list[dict], reserved_tokens: int = 0) -> list[dict]:
        budget = HISTORY_BUDGET - reserved_tokens
        system = [m for m in messages if m["role"] == "system"]
        history = [m for m in messages if m["role"] != "system"]
        while history and self._count_tokens(history) > budget:
            if len(history) >= 2: history = history[2:]
            else: history = []
        return system + history

    async def trim_with_summary(self, messages: list[dict], reserved_tokens: int = 0) -> list[dict]:
        trimmed = self.trim_history(messages, reserved_tokens)
        budget = HISTORY_BUDGET - reserved_tokens
        if self._count_tokens(trimmed) <= budget: return trimmed
        from core.agents.summarizer_agent import SummarizerAgent
        from core.context.rules_parser import RulesParser
        summarizer = SummarizerAgent(RulesParser(), self)
        system = [m for m in trimmed if m.get("role") == "system"]
        history = [m for m in trimmed if m.get("role") != "system"]
        to_compress, to_keep = summarizer.compress_history(history, keep_last=4)
        if not to_compress: return trimmed
        summary_text = await summarizer.summarize(to_compress)
        summary_msg = {"role": "system", "content": f"[Earlier context summary]\n{summary_text}"}
        return system + [summary_msg] + to_keep

    def truncate_tool_output(self, output: str) -> str:
        tokens = self._count_tokens([{"role": "tool", "content": output}])
        if tokens <= TOOL_OUTPUT_MAX: return output
        return output[:TOOL_OUTPUT_MAX * 4] + "\n... [truncated]"

    def _count_tokens(self, messages: list[dict]) -> int:
        total = 0
        for m in messages:
            content = m.get("content") or ""
            if isinstance(content, str):
                total += len(self._enc.encode(content))
        return total

    def _budget_chunks(self, chunks: list[dict], budget: int) -> list[dict]:
        result, used = [], 0
        for chunk in chunks:
            t = len(self._enc.encode(chunk["document"]))
            if used + t > budget: break
            result.append(chunk)
            used += t
        return result

import asyncio # Ensure asyncio is imported for to_thread
