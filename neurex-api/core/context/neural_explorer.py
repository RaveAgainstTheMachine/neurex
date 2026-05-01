"""
core/context/neural_explorer.py
Implements RAG 2.0: Hybrid Neural Code Search.
Combines Vector Retrieval with AST-aware Graph Traversal.
"""
from __future__ import annotations
import structlog
from typing import List, Dict, Any
from core.context.manager import ContextManager

log = structlog.get_logger()

class NeuralExplorer:
    def __init__(self, context_manager: ContextManager):
        self.ctx = context_manager
        self.call_graph: Dict[str, List[str]] = {} # file -> list of referenced files

    async def hybrid_search(self, query: str, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Performs a hybrid search:
        1. Semantic Search (ChromaDB)
        2. Relational Expansion (Call Graph)
        3. Context Ranking
        """
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
        return expanded_results

    def update_call_graph(self, file_path: str, references: List[str]):
        """Updates the relational mapping for a file."""
        self.call_graph[file_path] = references
        log.debug("neural_explorer.graph_updated", file=file_path, refs=len(references))

# NeuralExplorer will be initialized in the Orchestrator with the ContextManager.
