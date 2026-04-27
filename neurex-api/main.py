"""
neurex-api — main.py
Entry point: mounts routers, starts background workers, manages lifespan.
"""
from contextlib import asynccontextmanager
import structlog
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from dotenv import load_dotenv

load_dotenv()


from core.memory.worker import MemoryWorker
from core.context.rules_parser import RulesParser
from api.routes import chat, tasks, files, infra, notifications, skills, settings, auth, memory, update, observability
from api.websocket import router as ws_router
from core.task_graph import init_db
from core.logger import setup_logging

setup_logging()
log = structlog.get_logger()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup / shutdown lifecycle."""
    log.info("neurex.startup")

    # Initialise SQLite task-graph DB
    await init_db()

    # Start file-watcher + indexing worker
    memory_worker = MemoryWorker()
    await memory_worker.start()
    app.state.memory_worker = memory_worker

    # Load .neurexrules on startup
    rules = RulesParser()
    app.state.rules = rules

    # Initialise PTY Manager
    from core.terminal.pty_manager import PTYManager
    pty_manager = PTYManager()
    app.state.pty_manager = pty_manager

    # Start Insomnia Service
    from core.infrastructure.insomnia import insomnia_service
    insomnia_service.sync()

    # Start Distributed RPC Server
    from core.infrastructure.distributed import distributed_manager
    await distributed_manager.start_rpc_server()

    # Firewall Integrity Check + Sentinel (Auto-Healing)
    from core.infrastructure.firewall import firewall_manager
    import asyncio
    await firewall_manager.check_startup()
    asyncio.create_task(firewall_manager.start_sentinel())

    # Start Mesh Monitoring
    from core.infrastructure.mesh import mesh_router
    asyncio.create_task(mesh_router.start_monitoring())

    # Trigger initial hardware benchmark
    from core.infrastructure.benchmarker import benchmarker
    asyncio.create_task(benchmarker.run_benchmark())

    log.info("neurex.ready")
    yield

    # Teardown
    await memory_worker.stop()
    pty_manager.close_all()
    log.info("neurex.shutdown")


app = FastAPI(
    title="Neurex API",
    version="0.1.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origin_regex=r"https?://(localhost|127\.0\.0\.1|10\.\d+\.\d+\.\d+|192\.168\.\d+\.\d+|.*\.local):3000",
    allow_origins=[
        "http://10.10.10.48:3000",
        "https://10.10.10.48:3000",
        "http://localhost:3000",
        "http://127.0.0.1:3000",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ── Routes ──────────────────────────────────────────────────────────────────
app.include_router(chat.router, prefix="/api/chat", tags=["chat"])
app.include_router(tasks.router, prefix="/api/tasks", tags=["tasks"])
app.include_router(files.router, prefix="/api/files", tags=["files"])
app.include_router(infra.router, prefix="/api/infra", tags=["infra"])
app.include_router(notifications.router, prefix="/api/notifications", tags=["notifications"])
app.include_router(skills.router, prefix="/api/skills", tags=["skills"])
app.include_router(settings.router, prefix="/api/settings", tags=["settings"])
app.include_router(auth.router, prefix="/api/auth", tags=["auth"])
app.include_router(memory.router, prefix="/api/memory", tags=["memory"])
app.include_router(update.router)
app.include_router(observability.router)
app.include_router(ws_router, tags=["websocket"])


@app.get("/health")
async def health():
    return {"status": "ok", "version": "0.1.0"}


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    log.error("unhandled_exception", path=request.url.path, error=str(exc))
    return JSONResponse(status_code=500, content={"detail": "Internal server error"})
