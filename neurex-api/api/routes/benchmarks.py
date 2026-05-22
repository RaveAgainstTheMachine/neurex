"""
api/routes/benchmarks.py
Endpoints for running and tracking local simulation benchmarks (run_evals.py).
"""
import asyncio
import os
import sys
import time
from pathlib import Path

import structlog
from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException

from api.routes.auth import UserRole, require_role

log = structlog.get_logger()
router = APIRouter()

# Global memory state for tracking benchmark execution
BENCHMARK_STATE = {
    "status": "idle",       # "idle", "running", "completed", "failed"
    "current_case": None,   # name of currently running case
    "log": [],              # raw console output lines
    "results": [],          # parsed results for each run case
    "score": "0/0",
    "percentage": 0,
    "duration_s": 0.0,
    "start_time": 0.0,
    "error_details": None
}

_LOCK = asyncio.Lock()


async def run_benchmark_task(tag: str | None = None):
    global BENCHMARK_STATE
    async with _LOCK:
        BENCHMARK_STATE["status"] = "running"
        BENCHMARK_STATE["current_case"] = "Initializing"
        BENCHMARK_STATE["log"] = []
        BENCHMARK_STATE["results"] = []
        BENCHMARK_STATE["score"] = "0/0"
        BENCHMARK_STATE["percentage"] = 0
        BENCHMARK_STATE["duration_s"] = 0.0
        BENCHMARK_STATE["start_time"] = time.time()
        BENCHMARK_STATE["error_details"] = None

    # Get absolute path to project root and eval script
    project_root = Path(__file__).parent.parent.parent.resolve()
    eval_script = project_root / "eval" / "run_evals.py"

    cmd = [sys.executable, str(eval_script)]
    if tag:
        cmd.extend(["--only", tag])

    log.info("benchmark.start", cmd=cmd)

    try:
        process = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            cwd=str(project_root),
            env=os.environ.copy()
        )

        # Read stdout line by line
        while True:
            line_bytes = await process.stdout.readline()
            if not line_bytes:
                break
            line = line_bytes.decode("utf-8").rstrip()
            if not line:
                continue

            async with _LOCK:
                BENCHMARK_STATE["log"].append(line)

            # Parse lines to extract progress
            # e.g., "  smoke-hello                        ✅ PASS  (1.23s)"
            # or    "  py-fibonacci                       ❌ FAIL  (Missing: ...)"
            stripped = line.strip()
            if stripped.startswith("🧪"):
                pass
            elif "✅ PASS" in line or "❌ FAIL" in line:
                parts = stripped.split()
                if len(parts) >= 3:
                    case_id = parts[0]
                    passed = "✅" in line
                    
                    # Extract duration
                    duration = 0.0
                    for part in parts:
                        if part.endswith("s)") and part.startswith("("):
                            try:
                                duration = float(part[1:-2])
                            except ValueError:
                                pass

                    details = ""
                    if "❌ FAIL" in line:
                        idx = stripped.find("❌ FAIL")
                        if idx != -1:
                            details = stripped[idx + 7:].strip().strip("()")

                    result_item = {
                        "id": case_id,
                        "passed": passed,
                        "duration_s": duration,
                        "details": details
                    }
                    async with _LOCK:
                        BENCHMARK_STATE["results"].append(result_item)
                        BENCHMARK_STATE["current_case"] = f"Finished {case_id}"
            elif stripped.startswith("Score:"):
                # e.g., "Score: 2/2  (100%)"
                parts = stripped.split()
                if len(parts) >= 2:
                    score = parts[1]
                    percent = 0
                    for p in parts:
                        if p.endswith("%)") and p.startswith("("):
                            try:
                                percent = int(p[1:-2])
                            except ValueError:
                                pass
                    async with _LOCK:
                        BENCHMARK_STATE["score"] = score
                        BENCHMARK_STATE["percentage"] = percent

        await process.wait()

        # Gather stderr logs if any
        stderr_bytes = await process.stderr.read()
        if stderr_bytes:
            stderr_str = stderr_bytes.decode("utf-8").rstrip()
            if stderr_str:
                async with _LOCK:
                    BENCHMARK_STATE["log"].append("stderr: " + stderr_str)

        async with _LOCK:
            BENCHMARK_STATE["status"] = "completed"
            BENCHMARK_STATE["current_case"] = None
            BENCHMARK_STATE["duration_s"] = round(time.time() - BENCHMARK_STATE["start_time"], 2)

    except Exception as e:
        log.error("benchmark.error", error=str(e), exc_info=True)
        async with _LOCK:
            BENCHMARK_STATE["status"] = "failed"
            BENCHMARK_STATE["current_case"] = None
            BENCHMARK_STATE["error_details"] = str(e)
            BENCHMARK_STATE["duration_s"] = round(time.time() - BENCHMARK_STATE["start_time"], 2)


@router.post("/run", dependencies=[Depends(require_role(UserRole.DEVELOPER))])
async def run_benchmark(background_tasks: BackgroundTasks, tag: str | None = None):
    """Trigger an evaluation benchmark run."""
    global BENCHMARK_STATE
    async with _LOCK:
        if BENCHMARK_STATE["status"] == "running":
            raise HTTPException(status_code=400, detail="Benchmark is already running")

    background_tasks.add_task(run_benchmark_task, tag)
    return {"status": "ok", "message": "Benchmark execution triggered successfully"}


@router.get("/status", dependencies=[Depends(require_role(UserRole.DEVELOPER))])
async def get_benchmark_status():
    """Retrieve the current state and results of the benchmark execution."""
    async with _LOCK:
        return BENCHMARK_STATE
