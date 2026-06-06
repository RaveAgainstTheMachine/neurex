"""
core/context/manager.py
Dynamic context manager. Handles RAG retrieval and token budgets.
Gracefully degrades if ChromaDB or embedder is unavailable.
"""

from __future__ import annotations

import asyncio
import os

import structlog

log = structlog.get_logger()

CHROMA_DB_DIR = os.getenv("CHROMA_DB_DIR", "/games/AI/chroma_db")
COLLECTION = "neurex_codebase"


class ContextManager:
    def __init__(self):
        self._chroma = None
        self._collection = None
        self._embedder = None
        self._reranker = None
        self._enc = None
        self._available = False
        self.debate_verdicts: dict[str, str] = {}

        try:
            import tiktoken

            self._enc = tiktoken.get_encoding("cl100k_base")
        except Exception:
            log.warning("context.tiktoken_unavailable", hint="Token counting disabled")

        try:
            from core.context.neural_explorer import NeuralExplorer
            from core.memory.embedder import Embedder, Reranker

            self._embedder = Embedder()
            self._reranker = Reranker()
            self.explorer = NeuralExplorer(self)
        except Exception as e:
            log.warning("context.embedder_unavailable", error=str(e))
            self.explorer = None  # Fallback

    def _get_collection(self):
        """Synchronous retrieval of collection from PersistentClient."""
        if self._chroma is None:
            try:
                import chromadb

                self._chroma = chromadb.PersistentClient(path=CHROMA_DB_DIR)
                self._collection = self._chroma.get_or_create_collection(COLLECTION)
                self._available = True
            except Exception as e:
                log.warning("context.chroma_unavailable", error=str(e))
                self._available = False
        return self._collection

    def get_budgets(self, model_name: str | None = None) -> dict[str, int]:
        cw = 8192
        if model_name:
            from core.infrastructure.manager import infrastructure_manager

            registry = infrastructure_manager.get_merged_registry()
            for m in registry:
                name = m.get("name", "")
                if name == model_name or name.split(":")[0] == model_name.split(":")[0]:
                    cw = m.get("context_window", cw)
                    break

        sys = min(2000, int(cw * 0.15))
        rag = min(8000, int(cw * 0.25))
        tool = min(2000, int(cw * 0.1))
        hist = max(1000, cw - sys - rag - 512)

        return {
            "CONTEXT_WINDOW": cw,
            "SYSTEM_BUDGET": sys,
            "RAG_BUDGET": rag,
            "TOOL_OUTPUT_MAX": tool,
            "HISTORY_BUDGET": hist,
        }

    async def retrieve(
        self, query: str, n_results: int = 20, model_name: str | None = None
    ) -> list[dict]:
        """Embed → ANN search → rerank → return top-k within budget."""
        if os.getenv("NEUREX_MOCK_LLM") == "true":
            return []

        if not self._embedder:
            return []

        rag_budget = self.get_budgets(model_name)["RAG_BUDGET"]

        try:
            embedding = await self._embedder.embed(query)

            def query_sync():
                collection = self._get_collection()
                if collection is None:
                    return None
                return collection.query(
                    query_embeddings=[embedding],
                    n_results=min(n_results, 20),
                    include=["documents", "metadatas", "distances"],
                )

            results = await asyncio.to_thread(query_sync)
            if results is None:
                return []

            candidates = [
                {"document": doc, "metadata": meta, "distance": dist}
                for doc, meta, dist in zip(
                    results["documents"][0],
                    results["metadatas"][0],
                    results["distances"][0],
                )
            ]

            if self._reranker:
                reranked = self._reranker.rerank(query, candidates, top_k=10)
                return self._budget_chunks(reranked, rag_budget)
            return self._budget_chunks(candidates[:10], rag_budget)

        except Exception as e:
            log.error("context.retrieve_error", error=str(e))
            return []

    def trim_history(
        self, messages: list[dict], reserved_tokens: int = 0, model_name: str | None = None
    ) -> list[dict]:
        budget = self.get_budgets(model_name)["HISTORY_BUDGET"] - reserved_tokens
        system = [m for m in messages if m["role"] == "system"]
        history = [m for m in messages if m["role"] != "system"]
        while history and self._count_tokens(history) > budget:
            if len(history) >= 2:
                history = history[2:]
            else:
                history = []
        return system + history

    async def trim_with_summary(
        self, messages: list[dict], reserved_tokens: int = 0, model_name: str | None = None
    ) -> list[dict]:
        trimmed = self.trim_history(messages, reserved_tokens, model_name)
        budget = self.get_budgets(model_name)["HISTORY_BUDGET"] - reserved_tokens
        if self._count_tokens(trimmed) <= budget:
            return trimmed
        from core.agents.summarizer_agent import SummarizerAgent
        from core.context.rules_parser import RulesParser

        summarizer = SummarizerAgent(RulesParser(), self)
        system = [m for m in trimmed if m.get("role") == "system"]
        history = [m for m in trimmed if m.get("role") != "system"]
        to_compress, to_keep = summarizer.compress_history(history, keep_last=4)
        if not to_compress:
            return trimmed
        summary_text = await summarizer.summarize(to_compress)
        summary_msg = {"role": "system", "content": f"[Earlier context summary]\n{summary_text}"}
        return system + [summary_msg] + to_keep

    def truncate_tool_output(self, output: str, model_name: str | None = None) -> str:
        max_tool = self.get_budgets(model_name)["TOOL_OUTPUT_MAX"]
        tokens = self._count_tokens([{"role": "tool", "content": output}])
        if tokens <= max_tool:
            return output
        return output[: max_tool * 4] + "\n... [truncated]"

    def _count_tokens(self, messages: list[dict]) -> int:
        if not self._enc:
            # Rough estimate: 4 chars per token
            return sum(len(m.get("content") or "") // 4 for m in messages)
        total = 0
        for m in messages:
            content = m.get("content") or ""
            if isinstance(content, str):
                total += len(self._enc.encode(content))
        return total

    def _budget_chunks(self, chunks: list[dict], budget: int) -> list[dict]:
        result, used = [], 0
        for chunk in chunks:
            t = self._count_tokens([{"content": chunk["document"]}])
            if used + t > budget:
                break
            result.append(chunk)
            used += t
        return result
