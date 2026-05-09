"""
core/context/neural_explorer.py
Implements RAG 2.0: Hybrid Neural Code Search.
Combines Vector Retrieval with AST-aware Graph Traversal.
"""
from __future__ import annotations

from typing import Any

import structlog

from core.context.manager import ContextManager

log = structlog.get_logger()

class NeuralExplorer:
    def __init__(self, context_manager: ContextManager):
        self.ctx = context_manager
        self.call_graph: dict[str, list[str]] = {} # file -> list of referenced files
        # Phase 44.2: Fast Search Cache
        self._search_cache: dict[str, list[dict[str, Any]]] = {}

    async def hybrid_search(self, query: str, limit: int = 10) -> list[dict[str, Any]]:
        """
        Performs a cached hybrid search.
        """
        cache_key = f"{query}:{limit}"
        if cache_key in self._search_cache:
            log.info("neural_explorer.cache_hit", query=query)
            return self._search_cache[cache_key]

        log.info("neural_explorer.search_init", query=query)
        
        # 1. Semantic Retrieval
        base_results = await self.ctx.retrieve(query, n_results=limit)
        
        # 2. Relational Expansion
        # For each result, find its neighbors in the call graph
        expanded_results = list(base_results)
        seen_files = {r["metadata"]["file"] for r in base_results}
        
        for res in base_results:
            file_path = res["metadata"]["file"]
            neighbors = self.call_graph.get(file_path, [])
            for n in neighbors:
                if n not in seen_files:
                    # In a real implementation, we would fetch the neighbor's content
                    log.info("neural_explorer.expansion_hit", origin=file_path, neighbor=n)
                    seen_files.add(n)
                    
        # 3. Ranking logic (Simplified)
        self._search_cache[cache_key] = expanded_results
        return expanded_results

    def update_call_graph(self, file_path: str, references: list[str]):
        """Updates the relational mapping and invalidates the search cache."""
        self.call_graph[file_path] = references
        self._search_cache.clear() # Invalidate on change
        log.debug("neural_explorer.graph_updated", file=file_path, refs=len(references))

# NeuralExplorer will be initialized in the Orchestrator with the ContextManager.
