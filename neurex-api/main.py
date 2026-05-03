"""
neurex-api — main.py
Entry point: mounts routers, starts background workers, manages lifespan.
"""
from contextlib import asynccontextmanager
import asyncio
import structlog
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from dotenv import load_dotenv

load_dotenv()


from core.memory.worker import MemoryWorker
from core.context.rules_parser import RulesParser
from api.routes import chat, tasks, files, infra, notifications, skills, settings, auth, memory, update, observability, git, languages, evolution, singularity, synthesis, consensus, temporal
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

    # Start file-watcher + indexing worker (non-blocking)
    memory_worker = MemoryWorker()
    asyncio.create_task(memory_worker.start())
    app.state.memory_worker = memory_worker

    # Load .neurexrules on startup
    rules = RulesParser()
    app.state.rules = rules

    # Initialise PTY Manager
    from core.terminal.pty_manager import PTYManager
    pty_manager = PTYManager()
    app.state.pty_manager = pty_manager

    # Start Presence Manager tasks
    from core.collaboration.presence import presence_manager
    presence_manager.start()

    # Start Insomnia Service
    from core.infrastructure.insomnia import insomnia_service
    insomnia_service.sync()

    # Start File Watcher
    from core.infrastructure.watcher import watcher_service
    watcher_service.start()

    # Start Distributed RPC Server
    from core.infrastructure.distributed import distributed_manager
    await distributed_manager.start_rpc_server()

    # Firewall Integrity Check + Sentinel (Auto-Healing)
    from core.infrastructure.firewall import firewall_manager
    await firewall_manager.check_startup()
    asyncio.create_task(firewall_manager.start_sentinel())

    # Start Mesh Monitoring
    from core.infrastructure.mesh import mesh_router
    asyncio.create_task(mesh_router.start_monitoring())

    # Start Service Sentinel (Self-Healing)
    from core.observability.service_sentinel import sentinel as service_sentinel
    await service_sentinel.start()

    # Phase 55: Proactive LLM Health Check
    from core.infrastructure.manager import infrastructure_manager
    ollama_running = await infrastructure_manager._is_process_running("ollama")
    if not ollama_running:
        log.info("neurex.infra_startup", engine="ollama", msg="Attempting to start Ollama...")
        try:
            await infrastructure_manager.start_engine("ollama")
        except Exception as e:
            log.error("neurex.infra_startup_failed", engine="ollama", error=str(e))

    # Start CI/CD Healer (External Self-Healing)
    from core.observability.ci_healer import ci_healer
    asyncio.create_task(ci_healer.check_pipeline_health())

    # Trigger initial hardware benchmark
    from core.infrastructure.benchmarker import hardware_benchmarker
    
    # Phase 44.9: Start Flight Recorder Batch Worker
    from core.observability.flight_recorder import flush_decisions
    asyncio.create_task(flush_decisions())
    
    log.info("lsp.init_start")
    # Initialise LSP Manager
    from core.languages.lsp_manager import lsp_manager
    app.state.lsp_manager = lsp_manager
    
    # Pre-emptively start LSPs for workspace languages
    from api.routes.files import get_workspace
    workspace_path = str(get_workspace())
    log.info("lsp.workspace_sync", path=workspace_path)
    asyncio.create_task(lsp_manager.initialize_workspace(workspace_path))
    log.info("lsp.init_queued")

    log.info("neurex.ready")
    yield

    # Teardown
    try:
        if hasattr(app.state, "lsp_manager"):
            await app.state.lsp_manager.cleanup()
        if hasattr(app.state, "memory_worker"):
            await app.state.memory_worker.stop()
        if hasattr(app.state, "pty_manager"):
            app.state.pty_manager.close_all()
    except Exception as e:
        log.error("neurex.shutdown_error", error=str(e))
    log.info("neurex.shutdown")


from fastapi.responses import ORJSONResponse

app = FastAPI(
    title="Neurex Neural Mesh",
    description="Decentralized Autonomous Agentic Infrastructure",
    version="0.2.1-stable",
    lifespan=lifespan,
    default_response_class=ORJSONResponse
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
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
app.include_router(update.router, prefix="/api/update", tags=["update"])
app.include_router(observability.router, prefix="/api/observability", tags=["observability"])
app.include_router(languages.router, prefix="/api/languages", tags=["languages"])
app.include_router(git.router, prefix="/api/git", tags=["git"])
app.include_router(evolution.router)
app.include_router(singularity.router)
app.include_router(synthesis.router)
app.include_router(consensus.router)
app.include_router(temporal.router)
app.include_router(ws_router, tags=["websocket"])


@app.get("/health")
async def health():
    return {"status": "ok", "version": "0.1.0"}


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    log.error("unhandled_exception", path=request.url.path, error=str(exc))
    return JSONResponse(status_code=500, content={"detail": "Internal server error"})
