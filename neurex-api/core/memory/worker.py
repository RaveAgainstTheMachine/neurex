"""
core/memory/worker.py
Background worker that indexes the workspace into ChromaDB.
Modified to support local PersistentClient when running without Docker.
"""
from __future__ import annotations
import asyncio
import os
from pathlib import Path
import structlog
import chromadb
from chromadb.config import Settings
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

from core.memory.chunker import chunk_file
from core.memory.embedder import Embedder

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
        self.embedder = Embedder()
        self._observer: Observer | None = None
        self._chroma = None
        self._collection = None
        self._queue: asyncio.Queue[Path] = asyncio.Queue()
        self._loop: asyncio.AbstractEventLoop | None = None

    async def start(self):
        self._loop = asyncio.get_event_loop()
        
        # Rule: Use PersistentClient for local non-docker storage
        log.info("memory_worker.init_chroma", path=CHROMA_DB_DIR)
        
        # PersistentClient is synchronous, wrap in thread to keep startup snappy
        def init_sync():
            client = chromadb.PersistentClient(path=CHROMA_DB_DIR)
            collection = client.get_or_create_collection(
                COLLECTION,
                metadata={"hnsw:space": "cosine"},
            )
            return client, collection

        self._chroma, self._collection = await asyncio.to_thread(init_sync)

        # Start file watcher
        handler = _ChangeHandler(self._queue, self._loop)
        self._observer = Observer()
        self._observer.schedule(handler, str(WORKSPACE_PATH), recursive=True)
        self._observer.start()

        # Initial index in background
        asyncio.create_task(self._full_index())
        asyncio.create_task(self._process_queue())

        log.info("memory_worker.started", workspace=str(WORKSPACE_PATH))

    async def stop(self):
        if self._observer:
            self._observer.stop()
            self._observer.join()
        log.info("memory_worker.stopped")

    async def _full_index(self):
        log.info("memory_worker.full_index.start")
        count = 0
        for path in WORKSPACE_PATH.rglob("*"):
            if self._should_index(path):
                await self._index_file(path)
                count += 1
                await asyncio.sleep(0)
        log.info("memory_worker.full_index.done", files=count)

    async def _process_queue(self):
        while True:
            path = await self._queue.get()
            if self._should_index(path):
                await self._index_file(path)
            self._queue.task_done()

    async def _index_file(self, path: Path):
        try:
            chunks = chunk_file(path)
            if not chunks:
                return
            embeddings = await self.embedder.embed_batch([c["text"] for c in chunks])

            ids       = [f"{path}::{c['id']}" for c in chunks]
            documents = [c["text"] for c in chunks]
            metadatas = [c["metadata"] for c in chunks]

            # Upsert is synchronous in PersistentClient, offload to thread
            def upsert_sync():
                self._collection.upsert(
                    ids=ids,
                    embeddings=embeddings,
                    documents=documents,
                    metadatas=metadatas,
                )
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

class _ChangeHandler(FileSystemEventHandler):
    def __init__(self, queue: asyncio.Queue, loop: asyncio.AbstractEventLoop):
        self._queue = queue
        self._loop = loop

    def on_modified(self, event):
        if not event.is_directory:
            self._loop.call_soon_threadsafe(self._queue.put_nowait, Path(event.src_path))

    def on_created(self, event):
        if not event.is_directory:
            self._loop.call_soon_threadsafe(self._queue.put_nowait, Path(event.src_path))
