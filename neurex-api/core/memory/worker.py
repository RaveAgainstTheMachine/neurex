"""
core/memory/worker.py
Background worker that indexes the workspace into ChromaDB.
Gracefully degrades if ChromaDB is unavailable — logs once and disables indexing.
"""
from __future__ import annotations

import asyncio
import os
from pathlib import Path

import structlog

log = structlog.get_logger()

WORKSPACE_PATH = Path(os.getenv("WORKSPACE_PATH", "/workspace"))
CHROMA_DB_DIR  = os.getenv("CHROMA_DB_DIR", "/games/AI/chroma_db")
COLLECTION     = "neurex_codebase"

INDEXABLE_EXTENSIONS = {
    ".py", ".ts", ".tsx", ".js", ".jsx",
    ".go", ".rs", ".java", ".cpp", ".c", ".h",
    ".md", ".txt", ".yaml", ".yml", ".toml", ".json",
}

IGNORED_DIRS = {
    ".git", "node_modules", "__pycache__", ".neurex_trash",
    "dist", "build", ".venv", "venv",
}


class MemoryWorker:
    def __init__(self):
        self._observer = None
        self._chroma = None
        self._collection = None
        self._queue: asyncio.Queue[Path] = asyncio.Queue()
        self._loop: asyncio.AbstractEventLoop | None = None
        self._enabled = False
        self.summarizer = None

    async def start(self):
        self._loop = asyncio.get_event_loop()

        # Try to connect to ChromaDB — gracefully degrade if unavailable
        try:
            import chromadb

            from core.memory.embedder import Embedder

            log.info("memory_worker.init_chroma", path=CHROMA_DB_DIR)

            def init_sync():
                client = chromadb.PersistentClient(path=CHROMA_DB_DIR)
                collection = client.get_or_create_collection(
                    COLLECTION,
                    metadata={"hnsw:space": "cosine"},
                )
                return client, collection

            self._chroma, self._collection = await asyncio.to_thread(init_sync)
            self.embedder = Embedder()
            from core.memory.summarizer import Summarizer
            self.summarizer = Summarizer()
            self._enabled = True
            log.info("memory_worker.chroma_connected")

        except Exception:
            # Silent fallback for environments without ChromaDB or incompatible dependencies (Python 3.14)
            self._enabled = False
            log.info("memory_worker.disabled", reason="ChromaDB unavailable or dependency mismatch")
            return

        # Start file watcher
        try:
            handler = _ChangeHandler(self._queue, self._loop)
            self._observer = Observer()
            self._observer.schedule(handler, str(WORKSPACE_PATH), recursive=True)
            self._observer.start()
        except Exception as e:
            log.warning("memory_worker.watcher_failed", error=str(e))

        # Initial index in background
        asyncio.create_task(self._full_index())
        asyncio.create_task(self._process_queue())

        log.info("memory_worker.started", workspace=str(WORKSPACE_PATH))

    async def stop(self):
        if self._observer and self._observer.is_alive():
            self._observer.stop()
            self._observer.join()
        log.info("memory_worker.stopped")

    async def _full_index(self):
        """Phase 44.12: Sema-Throttled Parallel Indexing."""
        if not self._enabled:
            return
        
        log.info("memory_worker.full_index.start")
        # Throttle to avoid CPU/API exhaustion
        semaphore = asyncio.Semaphore(10)
        
        async def indexed_task(path):
            async with semaphore:
                await self._index_file(path)

        all_paths = [p for p in WORKSPACE_PATH.rglob("*") if self._should_index(p)]
        if all_paths:
            await asyncio.gather(*[indexed_task(p) for p in all_paths])
            
        log.info("memory_worker.full_index.done", files=len(all_paths))

    async def _process_queue(self):
        while True:
            path = await self._queue.get()
            if self._enabled and self._should_index(path):
                await self._index_file(path)
            self._queue.task_done()

    async def _index_file(self, path: Path):
        if not self._enabled:
            return
        try:
            from core.memory.chunker import chunk_file
            chunks = chunk_file(path)
            if not chunks:
                return
            documents = []
            for i, chunk in enumerate(chunks):
                # Enrich first chunk (headers) and definitions (class/def)
                if i == 0 or "class " in chunk["text"] or "def " in chunk["text"]:
                    summary = await self.summarizer.summarize_chunk(chunk["text"])
                    if summary:
                        documents.append(f"ANALYSIS: {summary}\n\nCODE:\n{chunk['text']}")
                    else:
                        documents.append(chunk["text"])
                else:
                    documents.append(chunk["text"])

            embeddings = await self.embedder.embed_batch(documents)
            if not embeddings:
                log.warning("memory_worker.skip_file", file=str(path), reason="Embedding failed")
                return

            ids       = [f"{path}::{c['id']}" for c in chunks]
            metadatas = [c["metadata"] for c in chunks]

            def upsert_sync():
                try:
                    self._collection.upsert(
                        ids=ids,
                        embeddings=embeddings,
                        documents=documents,
                        metadatas=metadatas,
                    )
                except Exception as e:
                    log.error("memory_worker.upsert_failed", file=str(path), error=str(e))

            await asyncio.to_thread(upsert_sync)
            log.debug("memory_worker.indexed", file=str(path), chunks=len(chunks))
        except Exception as e:
            log.error("memory_worker.index_error", file=str(path), error=str(e))

    def _should_index(self, path: Path) -> bool:
        if not path.is_file():
            return False
        if path.suffix not in INDEXABLE_EXTENSIONS:
            return False
        for part in path.parts:
            if part in IGNORED_DIRS:
                return False
        return True


try:
    from watchdog.events import FileSystemEventHandler
    from watchdog.observers import Observer

    class _ChangeHandler(FileSystemEventHandler):
        """Watchdog event handler that enqueues changed files for re-indexing."""
        def __init__(self, queue: asyncio.Queue, loop: asyncio.AbstractEventLoop):
            self._queue = queue
            self._loop = loop

        def on_modified(self, event):
            if not event.is_directory:
                self._loop.call_soon_threadsafe(self._queue.put_nowait, Path(event.src_path))

        def on_created(self, event):
            if not event.is_directory:
                self._loop.call_soon_threadsafe(self._queue.put_nowait, Path(event.src_path))
except ImportError:
    Observer = None
    FileSystemEventHandler = object
    _ChangeHandler = None
