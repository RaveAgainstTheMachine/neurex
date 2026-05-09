"""
core/memory/embedder.py
Embedding via Ollama (nomic-embed-text) + optional cross-encoder reranking.
"""
from __future__ import annotations

import os

import httpx
import structlog

log = structlog.get_logger()

def get_ollama_base():
    return os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")

def get_embed_model():
    return os.getenv("EMBED_MODEL", "nomic-embed-text")



class Embedder:
    async def embed(self, text: str) -> list[float]:
        return (await self.embed_batch([text]))[0]

    async def embed_batch(self, texts: list[str]) -> list[list[float]]:
        """Embed a batch of texts via Ollama."""
        embeddings = []
        try:
            async with httpx.AsyncClient(timeout=60) as client:
                for text in texts:
                    r = await client.post(
                        f"{get_ollama_base()}/api/embeddings",
                        json={"model": get_embed_model(), "prompt": text},
                    )
                    r.raise_for_status()
                    embeddings.append(r.json()["embedding"])
        except Exception as e:
            log.error("embedder.failed", error=str(e))
            # Return empty list or zeros? Empty list is safer for the caller to handle as "failure"
            return []
        return embeddings


class Reranker:
    """
    Cross-encoder reranker using sentence-transformers.
    Falls back gracefully if the model isn't available.
    """
    _model = None

    def _load(self):
        if self._model is None:
            try:
                import torch
                from sentence_transformers import CrossEncoder
                device = "cuda" if torch.cuda.is_available() else "cpu"
                log.info("reranker.loading", device=device)
                self._model = CrossEncoder("cross-encoder/ms-marco-MiniLM-L-6-v2", device=device)
            except Exception as e:
                log.warning("reranker.load_failed", error=str(e))
        return self._model

    def rerank(
        self, query: str, candidates: list[dict], top_k: int = 5
    ) -> list[dict]:
        """
        Rerank ChromaDB results by relevance.
        candidates: list of {"document": str, "metadata": dict, ...}
        """
        model = self._load()
        if model is None or not candidates:
            return candidates[:top_k]

        pairs = [(query, c["document"]) for c in candidates]
        try:
            scores = model.predict(pairs)
            ranked = sorted(
                zip(scores, candidates),
                key=lambda x: x[0],
                reverse=True,
            )
            return [c for _, c in ranked[:top_k]]
        except Exception as e:
            log.error("reranker.error", error=str(e))
            return candidates[:top_k]
