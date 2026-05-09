"""
core/memory/hive.py
Distributed Vector Memory (Hive Mind) for cross-conversation context.
"""
import os
from typing import Any

import chromadb
import structlog
from chromadb.utils import embedding_functions

log = structlog.get_logger()

# Workspace-local persistent storage
CHROMA_PATH = os.path.join(os.getcwd(), ".neurex", "memory", "hive")
os.makedirs(CHROMA_PATH, exist_ok=True)

class HiveMind:
    def __init__(self):
        self.client = chromadb.PersistentClient(path=CHROMA_PATH)
        # Using default SentenceTransformer for local embeddings
        self.ef = embedding_functions.DefaultEmbeddingFunction()
        self.collection = self.client.get_or_create_collection(
            name="hive_mind",
            embedding_function=self.ef,
            metadata={"hnsw:space": "cosine"}
        )

    def remember(self, content: str, metadata: dict[str, Any], doc_id: str):
        """Inject a memory into the global store."""
        try:
            self.collection.upsert(
                documents=[content],
                metadatas=[metadata],
                ids=[doc_id]
            )
            log.info("hive.remember", id=doc_id)
        except Exception as e:
            log.error("hive.remember_failed", error=str(e))

    def recall(self, query: str, limit: int = 5) -> list[dict[str, Any]]:
        """Search the collective memory for relevant context."""
        try:
            results = self.collection.query(
                query_texts=[query],
                n_results=limit
            )
            
            # Format results
            memories = []
            if results["documents"]:
                for i in range(len(results["documents"][0])):
                    memories.append({
                        "content": results["documents"][0][i],
                        "metadata": results["metadatas"][0][i],
                        "distance": results["distances"][0][i]
                    })
            return memories
        except Exception as e:
            log.error("hive.recall_failed", error=str(e))
            return []

hive_mind = HiveMind()
