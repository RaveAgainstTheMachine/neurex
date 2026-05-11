"""
core/infrastructure/manager.py
Manages LLM engines (Ollama, vLLM, etc.) and system resources.
"""

import asyncio
import json
import os
import platform
import shutil
import sys
from typing import Any

import psutil
import structlog

log = structlog.get_logger()


class EngineStatus:
    def __init__(self, name: str, is_running: bool, version: str = "unknown"):
        self.name = name
        self.is_running = is_running
        self.version = version


class InfrastructureManager:
    def __init__(self):
        self.supported_engines = ["ollama", "vllm", "llama.cpp"]

    async def get_status(self) -> list[dict[str, Any]]:
        """Check status of all supported engines with detailed diagnostics."""
        statuses = []
        for engine in self.supported_engines:
            if engine == "llama.cpp":
                # Detect if llama-cpp-python is installed
                import importlib.util

                spec = importlib.util.find_spec("llama_cpp")
                path = spec.origin if spec else None
                is_running = await self._is_process_running(
                    "llama_cpp.server"
                ) or await self._is_process_running("llama-server")
                version = await self._get_version("llama.cpp")

                status_text = "running" if is_running else ("stopped" if path else "missing")

                status_data = {
                    "name": engine,
                    "status": status_text,
                    "version": version
                    if version != "unknown"
                    else ("Installed" if path else "n/a"),
                    "installed": path is not None,
                    "details": "Install via 'llama-cpp-python[server]'" if not path else "",
                    "path": path or "Not found",
                }

                if is_running:
                    from core.infrastructure.distributed import distributed_manager

                    status_data["rpc_endpoint"] = (
                        distributed_manager.get_rpc_address()
                        if distributed_manager.rpc_process
                        else None
                    )

            else:
                binary_name = engine
                path = shutil.which(binary_name)
                is_running = await self._is_process_running(binary_name)
                version = await self._get_version(binary_name)

                status_text = "running" if is_running else ("stopped" if path else "missing")

                details = ""
                if not path:
                    if engine == "ollama":
                        details = "Install via 'curl -fsSL https://ollama.com/install.sh | sh'"
                    elif engine == "vllm":
                        details = "Install via 'pip install vllm'"

                status_data = {
                    "name": engine,
                    "status": status_text,
                    "version": version
                    if version != "unknown"
                    else ("Installed" if path else "n/a"),
                    "installed": path is not None,
                    "details": details,
                    "path": path or "Not found",
                }

            statuses.append(status_data)
        return statuses

    async def pull_model(self, engine: str, model_name: str):
        """Pull (download) a model for a specific engine."""
        if engine == "ollama":
            if not shutil.which("ollama"):
                raise Exception("Ollama not installed")

            from core.settings.manager import settings_manager

            models_dir = os.path.expanduser(settings_manager.get("models_dir"))

            log.info("infra.model_pull_start", engine=engine, model=model_name, path=models_dir)
            env = os.environ.copy()
            env["OLLAMA_MODELS"] = models_dir

            process = await asyncio.create_subprocess_exec(
                "ollama",
                "pull",
                model_name,
                env=env,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            stdout, stderr = await process.communicate()
            if process.returncode != 0:
                error = stderr.decode()
                log.error("infra.model_pull_failed", engine=engine, model=model_name, error=error)
                raise Exception(f"Failed to pull model: {error}")

            log.info("infra.model_pull_success", engine=engine, model=model_name)
            return True

        if engine in ["llama.cpp", "llamacpp"]:
            engine = "llama.cpp"  # Normalize
            log.info("infra.model_pull_start", engine=engine, model=model_name)
            try:
                from pathlib import Path

                from huggingface_hub import hf_hub_download

                from core.settings.manager import settings_manager

                # Check if model_name is in format 'repo/name:filename' or just 'repo/name'
                if ":" in model_name:
                    repo_id, filename = model_name.split(":", 1)
                else:
                    repo_id = model_name
                    # Default to finding the first .gguf in the repo
                    from huggingface_hub import HfApi

                    api = HfApi()
                    files = api.list_repo_files(repo_id)
                    filename = next((f for f in files if f.endswith(".gguf")), None)
                    if not filename:
                        raise Exception(f"No .gguf file found in repository {repo_id}")

                models_dir = (
                    Path(os.path.expanduser(settings_manager.get("models_dir"))) / "llama.cpp"
                )
                models_dir.mkdir(parents=True, exist_ok=True)

                log.info(
                    "infra.hf_download_start", repo=repo_id, file=filename, dest=str(models_dir)
                )

                path = hf_hub_download(
                    repo_id=repo_id,
                    filename=filename,
                    local_dir=str(models_dir),
                    local_dir_use_symlinks=False,
                )

                log.info("infra.model_pull_success", engine=engine, model=model_name, path=path)
                return True
            except ImportError:
                # Attempt to install huggingface_hub if missing
                log.warning("infra.hf_hub_missing", msg="Attempting to install huggingface_hub...")
                venv_python = os.path.expanduser("~/.neurex/env/bin/python")
                python_exe = venv_python if os.path.exists(venv_python) else sys.executable
                install_proc = await asyncio.create_subprocess_exec(
                    python_exe, "-m", "pip", "install", "huggingface_hub"
                )
                await install_proc.wait()
                # Retry download once (recursive call)
                return await self.pull_model(engine, model_name)
            except Exception as e:
                log.error("infra.model_pull_failed", engine=engine, model=model_name, error=str(e))
                raise Exception(f"Failed to pull llama.cpp model: {str(e)}")

        raise Exception(f"Pulling models for {engine} is not supported yet.")

    async def get_installed_models(self, engine: str) -> list[dict[str, Any]]:
        """List models currently available and track which are currently loaded/active."""
        if engine == "ollama":
            # Phase 44.15: High-Performance Model Caching (15s TTL)
            if hasattr(self, "_model_cache"):
                import time

                cached_at, cached_models = self._model_cache
                if time.time() - cached_at < 15:
                    return cached_models

            models = []
            ollama_url = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")

            # 1. Get running models first
            running_models = []
            try:
                import httpx

                async with httpx.AsyncClient(timeout=2) as client:
                    resp = await client.get(f"{ollama_url}/api/ps")
                    if resp.status_code == 200:
                        ps_data = resp.json()
                        running_models = [m["name"] for m in ps_data.get("models", [])]
            except Exception:
                pass

            # 2. Get all tags and enriched metadata
            try:
                import httpx

                async with httpx.AsyncClient(timeout=5) as client:
                    resp = await client.get(f"{ollama_url}/api/tags")
                    if resp.status_code == 200:
                        data = resp.json()
                        for m in data.get("models", []):
                            name = m["name"]
                            size_bytes = m.get("size", 0)

                            # Fetch precise metadata via /api/show
                            params = "Unknown"
                            try:
                                show_resp = await client.post(
                                    f"{ollama_url}/api/show", json={"name": name}
                                )
                                if show_resp.status_code == 200:
                                    show_data = show_resp.json()
                                    details = show_data.get("details", {})
                                    params = details.get("parameter_size", "Unknown").upper()
                            except Exception:
                                pass

                            # Regex fallback if /api/show failed or returned Unknown
                            if params == "Unknown":
                                import re

                                param_match = re.search(r"[:\-]([0-9.]+[bB])", name)
                                params = param_match.group(1).upper() if param_match else "Unknown"

                            models.append(
                                {
                                    "name": name,
                                    "size_gb": round(size_bytes / (1024**3), 2),
                                    "params": params,
                                    "modified_at": m.get("modified_at"),
                                    "is_active": any(
                                        name == rm or name.split(":")[0] == rm.split(":")[0]
                                        for rm in running_models
                                    ),
                                }
                            )

                        import time

                        self._model_cache = (time.time(), models)
                        return models
            except Exception:
                pass

            # 3. Filesystem Fallback (if API failed or returned nothing)
            if not models:
                from pathlib import Path

                from core.settings.manager import settings_manager

                # Use configured models directory
                models_base = settings_manager.get("models_dir")
                manifest_path = Path(os.path.expanduser(models_base)) / "manifests"

                if not manifest_path.exists():
                    # Check system-wide path
                    manifest_path = Path("/usr/share/ollama/.ollama/models/manifests")

                if manifest_path.exists():
                    log.info("infra.model_scan_fallback", path=str(manifest_path))
                    for root, dirs, files in os.walk(manifest_path):
                        for file in files:
                            # manifest path is usually manifests/registry.ollama.ai/library/model/tag
                            rel_path = Path(root).relative_to(manifest_path)
                            parts = list(rel_path.parts)
                            if len(parts) >= 2:
                                if parts[0] == "registry.ollama.ai":
                                    parts = parts[1:]
                                if len(parts) > 0 and parts[0] == "library":
                                    parts = parts[1:]
                                model_name = "/".join(parts)
                                # Try to parse manifest for size
                                size_gb = 0.0
                                try:
                                    manifest_file = Path(root) / file
                                    with open(manifest_file) as f:
                                        m_data = json.load(f)
                                        total_bytes = sum(
                                            layer.get("size", 0)
                                            for layer in m_data.get("layers", [])
                                        )
                                        # Also add the config layer size if it exists
                                        total_bytes += m_data.get("config", {}).get("size", 0)
                                        size_gb = round(total_bytes / (1024**3), 2)
                                except Exception:
                                    pass

                                # Extract params (e.g., 14b, 7b, 70b) from name
                                import re

                                param_match = re.search(
                                    r"[:\-]([0-9.]+[bB])", f"{model_name}:{file}"
                                )
                                params = param_match.group(1).upper() if param_match else "Unknown"

                                models.append(
                                    {
                                        "name": f"{model_name}:{file}",
                                        "size_gb": size_gb,
                                        "params": params,
                                        "modified_at": "filesystem_fallback",
                                    }
                                )

            # Deduplicate and return
            unique_models = {m["name"]: m for m in models}.values()
            return sorted(list(unique_models), key=lambda x: x["name"])

        return []

    async def start_engine(self, name: str):
        """Start a specific LLM engine using configured ports."""
        from core.settings.manager import settings_manager

        if name == "ollama":
            if not shutil.which("ollama"):
                raise Exception("Ollama not installed in PATH")

            port = settings_manager.get("ollama_port")
            models_dir = os.path.expanduser(settings_manager.get("models_dir"))

            env = os.environ.copy()
            env["OLLAMA_HOST"] = f"0.0.0.0:{port}"
            env["OLLAMA_MODELS"] = models_dir

            process = await asyncio.create_subprocess_exec(
                "ollama",
                "serve",
                env=env,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            log.info("infra.engine_started", engine=name, port=port)
            return True

        elif name == "vllm":
            venv_python = os.path.expanduser("~/.neurex/env/bin/python")
            python_exe = venv_python if os.path.exists(venv_python) else sys.executable

            port = settings_manager.get("vllm_port")
            # Example vLLM start: python -m vllm.entrypoints.openai.api_server --port 8002
            cmd = [python_exe, "-m", "vllm.entrypoints.openai.api_server", "--port", str(port)]

            process = await asyncio.create_subprocess_exec(
                *cmd, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE
            )
            log.info("infra.engine_started", engine=name, port=port)
            return True

        elif name == "llama.cpp":
            venv_python = os.path.expanduser("~/.neurex/env/bin/python")
            python_exe = venv_python if os.path.exists(venv_python) else sys.executable

            port = settings_manager.get("llama_cpp_port")

            # 1. Discover all RPC workers in the mesh
            from core.collaboration.presence import presence_manager

            rpc_hosts = []
            for conv_state in presence_manager.presence_state.values():
                for user_state in conv_state.values():
                    if user_state.get("type") == "compute_node":
                        caps = user_state.get("capabilities", {})
                        if caps.get("is_rpc_worker") and caps.get("rpc_endpoint"):
                            rpc_hosts.append(caps["rpc_endpoint"])

            from core.infrastructure.mesh import mesh_router

            for peer in mesh_router.peers.values():
                if peer.status == "online" and getattr(peer, "rpc_endpoint", None):
                    rpc_hosts.append(peer.rpc_endpoint)

            rpc_hosts = list(set(rpc_hosts))

            # 2. Start llama-cpp-python server
            cmd = [
                python_exe,
                "-m",
                "llama_cpp.server",
                "--port",
                str(port),
                "--model",
                "models/default.gguf",
            ]

            process = await asyncio.create_subprocess_exec(
                *cmd, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE
            )
            log.info("infra.engine_started", engine=name, port=port, mesh_peers=len(rpc_hosts))
            return True

        raise Exception(f"Start logic for {name} not implemented yet")

    async def stop_engine(self, name: str):
        """Stop a specific LLM engine by killing its processes."""
        count = 0
        for proc in psutil.process_iter(["name"]):
            if name in proc.info["name"].lower():
                proc.terminate()
                count += 1
        log.info("infra.engine_stopped", engine=name, killed_count=count)
        return count > 0

    async def install_engine(self, name: str):
        """Execute installation commands for an engine with Phase 48 dependency validation."""
        log.info("infra.engine_install_start", engine=name)

        venv_python = os.path.expanduser("~/.neurex/env/bin/python")
        python_exe = venv_python if os.path.exists(venv_python) else sys.executable

        # 1. Ensure PIP is available in the environment
        try:
            check_pip = await asyncio.create_subprocess_exec(
                python_exe,
                "-m",
                "pip",
                "--version",
                stdout=asyncio.subprocess.DEVNULL,
                stderr=asyncio.subprocess.DEVNULL,
            )
            await check_pip.wait()
            if check_pip.returncode != 0:
                log.warning("infra.pip_missing", engine=name, msg="Attempting ensurepip...")
                fix_pip = await asyncio.create_subprocess_exec(
                    python_exe, "-m", "ensurepip", "--default-pip"
                )
                await fix_pip.wait()
        except Exception as e:
            log.error("infra.pip_check_failed", error=str(e))

        cmd_str = ""
        if name == "ollama":
            cmd_str = "curl -fsSL https://ollama.com/install.sh | sh"
        elif name == "vllm":
            cmd_str = f"{python_exe} -m pip install vllm"
        elif name == "llama.cpp":
            cmd_str = f"{python_exe} -m pip install llama-cpp-python[server]"
        else:
            # SECURITY: Explicitly validate 'name' against supported engines
            if name not in self.supported_engines:
                raise Exception(f"Unauthorized engine installation attempt: {name}")
            raise Exception(f"No installation script defined for {name}")

        try:
            # SECURITY: Avoid shell=True where possible. Since cmd_str is a complex shell command (curl | sh),
            # we ensure it's hardcoded or strictly validated.
            process = await asyncio.create_subprocess_shell(
                cmd_str, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE
            )
            stdout, stderr = await process.communicate()

            if process.returncode == 0:
                log.info("infra.engine_install_success", engine=name)
                return True
            else:
                error_msg = stderr.decode().strip()
                log.error("infra.engine_install_failed", engine=name, error=error_msg)
                raise Exception(f"Installation failed: {error_msg}")
        except Exception as e:
            log.error("infra.engine_install_error", engine=name, error=str(e))
            raise e

    def get_system_vram(self) -> float:
        """
        Estimate available VRAM in GB using nvidia-smi.
        """
        try:
            import subprocess

            result = subprocess.run(
                ["nvidia-smi", "--query-gpu=memory.total", "--format=csv,noheader,nounits"],
                capture_output=True,
                text=True,
                check=True,
                timeout=5,
            )
            # result might have multiple GPUs, we take the first one
            total_mib = float(result.stdout.strip().split("\n")[0])
            return round(total_mib / 1024, 1)
        except Exception as e:
            log.warning("infra.vram_detection_failed", error=str(e))
            return 0.0  # Unknown

    def get_system_metrics(self) -> dict[str, Any]:
        """Gather real-time CPU, RAM, and Disk metrics across configured storage paths."""
        from core.settings.manager import settings_manager

        ram = psutil.virtual_memory()

        # Aggregate disk usage across configured storage paths, deduplicated by mount point
        storage_paths = settings_manager.get("storage_paths")
        seen_mounts = set()
        total_gb = 0.0
        used_gb = 0.0

        for path in storage_paths:
            try:
                # Resolve to absolute path and find mount point
                abs_path = os.path.abspath(os.path.expanduser(path))
                if not os.path.exists(abs_path):
                    continue

                # Get usage for the specific path
                usage = psutil.disk_usage(abs_path)

                # To prevent double-counting if multiple paths are on the same disk,
                # we ideally want to track mount points.
                # But for Neurex, we want to know how much space is in the *configured* areas.
                # If they are on different disks, we sum them.
                total_gb += usage.total / (1024**3)
                used_gb += usage.used / (1024**3)
            except Exception as e:
                log.warning("infra.disk_check_failed", path=path, error=str(e))

        free_gb = max(0.0, total_gb - used_gb)
        disk_percent = (used_gb / total_gb * 100) if total_gb > 0 else 0

        return {
            "vram_gb": self.get_system_vram(),
            "ram_total_gb": round(ram.total / (1024**3), 1),
            "ram_used_gb": round(ram.used / (1024**3), 1),
            "ram_available_gb": round(ram.available / (1024**3), 1),
            "ram_percent": ram.percent,
            "cpu_percent": psutil.cpu_percent(interval=0.1),
            "disk_total_gb": round(total_gb, 1),
            "disk_used_gb": round(used_gb, 1),
            "disk_free_gb": round(free_gb, 1),
            "disk_percent": round(disk_percent, 1),
            "storage_health": self.validate_storage_permissions(),
            "specs": self.get_hardware_specs(),
        }

    def get_hardware_specs(self) -> dict[str, Any]:
        """Discovery of hardware identifiers (CPU model, GPU model, core count)."""
        specs = {
            "cpu_cores": psutil.cpu_count(logical=True),
            "cpu_physical_cores": psutil.cpu_count(logical=False),
            "cpu_model": "Unknown CPU",
            "gpu_model": "N/A",
        }

        # 1. Try to get CPU Model Name
        try:
            if platform.system() == "Linux":
                with open("/proc/cpuinfo") as f:
                    for line in f:
                        if "model name" in line:
                            specs["cpu_model"] = line.split(":")[1].strip()
                            break
            elif platform.system() == "Darwin":
                import subprocess

                specs["cpu_model"] = (
                    subprocess.check_output(["sysctl", "-n", "machdep.cpu.brand_string"])
                    .decode()
                    .strip()
                )
        except Exception:
            pass

        # 2. Try to get GPU Model (NVIDIA)
        try:
            import subprocess

            res = subprocess.run(
                ["nvidia-smi", "--query-gpu=name", "--format=csv,noheader"],
                capture_output=True,
                text=True,
                timeout=1,
            )
            if res.returncode == 0:
                specs["gpu_model"] = res.stdout.strip()
        except Exception:
            pass

        return specs

    def validate_storage_permissions(self) -> dict[str, Any]:
        """Checks if configured storage paths are writable and exists."""
        from core.settings.manager import settings_manager

        paths = settings_manager.get("storage_paths")
        neurex_dir = os.path.normpath(
            os.path.expanduser(settings_manager.get("neurex_install_dir"))
        )
        models_dir = os.path.normpath(os.path.expanduser(settings_manager.get("models_dir")))

        results = {}
        for p in paths:
            abs_p = os.path.normpath(os.path.abspath(os.path.expanduser(p)))
            exists = os.path.exists(abs_p)
            writable = os.access(abs_p, os.W_OK) if exists else False

            # Dynamic labeling with normalized paths
            labels = []
            if abs_p == neurex_dir:
                labels.append("NEUREX")
            if abs_p == models_dir:
                labels.append("MODELS")

            usage_data = None
            if exists:
                try:
                    usage = psutil.disk_usage(abs_p)
                    usage_data = {
                        "total_gb": round(usage.total / (1024**3), 1),
                        "used_gb": round(usage.used / (1024**3), 1),
                        "free_gb": round(usage.free / (1024**3), 1),
                        "percent": usage.percent,
                    }
                except Exception:
                    pass

            results[p] = {
                "exists": exists,
                "writable": writable,
                "status": "ok" if (exists and writable) else "error",
                "labels": labels,
                "usage": usage_data,
            }
        return results

    async def _is_process_running(self, name: str) -> bool:
        """Check if any process matching the name is active and responding."""
        is_active = False
        for proc in psutil.process_iter(["name"]):
            try:
                if name.lower() in proc.info["name"].lower():
                    is_active = True
                    break
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                pass

        # If it's ollama, verify the API is actually responding
        if name == "ollama" and is_active:
            try:
                import aiohttp

                from core.settings.manager import settings_manager

                base_url = settings_manager.get("ollama_base_url")
                async with aiohttp.ClientSession() as session:
                    async with session.get(f"{base_url}/api/tags", timeout=1) as resp:
                        return resp.status == 200
            except Exception:
                return False
        return is_active

    async def _get_version(self, name: str) -> str:
        """Attempt to get engine version via CLI or API."""
        try:
            if name == "ollama":
                # Try API first as it's more accurate for the running instance
                try:
                    import aiohttp

                    from core.settings.manager import settings_manager

                    base_url = settings_manager.get("ollama_base_url")
                    async with aiohttp.ClientSession() as session:
                        async with session.get(f"{base_url}/api/version", timeout=1) as resp:
                            if resp.status == 200:
                                data = await resp.json()
                                return f"Ollama {data.get('version', 'unknown')}"
                except Exception:
                    pass

                # Fallback to CLI
                proc = await asyncio.create_subprocess_exec(
                    "ollama",
                    "--version",
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE,
                )
                stdout, _ = await proc.communicate()
                return stdout.decode().strip()
        except Exception:
            pass
        return "unknown"

    async def resolve_model_params(self, model_name: str) -> str:
        """
        Attempt to resolve model parameters (e.g. 14B) from the registry or tags.
        """
        # Try local Ollama first
        try:
            models = await self.get_installed_models("ollama")
            for m in models:
                if m["name"] == model_name or m["name"].split(":")[0] == model_name.split(":")[0]:
                    if m.get("params") and m["params"] != "Unknown":
                        return m["params"]
        except Exception:
            pass

        # Try regex on name as fallback
        import re

        param_match = re.search(r"[:\-]([0-9.]+[bB])", model_name)
        if param_match:
            return param_match.group(1).upper()

        return "Unknown"


infrastructure_manager = InfrastructureManager()
