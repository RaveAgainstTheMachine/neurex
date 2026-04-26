"""
core/infrastructure/manager.py
Manages LLM engines (Ollama, vLLM, etc.) and system resources.
"""
import asyncio
import shutil
import psutil
import structlog
from typing import Dict, List, Any

log = structlog.get_logger()

class EngineStatus:
    def __init__(self, name: str, is_running: bool, version: str = "unknown"):
        self.name = name
        self.is_running = is_running
        self.version = version

class InfrastructureManager:
    def __init__(self):
        self.supported_engines = ["ollama", "vllm", "llama.cpp"]

    async def get_status(self) -> List[Dict[str, Any]]:
        """Check status of all supported engines with detailed diagnostics."""
        statuses = []
        for engine in self.supported_engines:
            binary_name = engine
            if engine == "llama.cpp":
                binary_name = "llama-server"
            
            path = shutil.which(binary_name)
            is_running = self._is_process_running(binary_name)
            version = await self._get_version(binary_name)
            
            status_text = "running" if is_running else ("stopped" if path else "missing")
            
            details = ""
            if not path:
                if engine == "ollama":
                    details = "Install via 'curl -fsSL https://ollama.com/install.sh | sh'"
                elif engine == "vllm":
                    details = "Install via 'pip install vllm'"
                elif engine == "llama.cpp":
                    details = "Ensure 'llama-server' is in PATH"
            
            statuses.append({
                "name": engine,
                "status": status_text,
                "version": version if version != "unknown" else ("Installed" if path else "n/a"),
                "installed": path is not None,
                "details": details,
                "path": path or "Not found"
            })
        return statuses

    async def pull_model(self, engine: str, model_name: str):
        """Pull (download) a model for a specific engine."""
        if engine == "ollama":
            if not shutil.which("ollama"):
                raise Exception("Ollama not installed")
            
            log.info("infra.model_pull_start", engine=engine, model=model_name)
            process = await asyncio.create_subprocess_exec(
                "ollama", "pull", model_name,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            stdout, stderr = await process.communicate()
            if process.returncode != 0:
                error = stderr.decode()
                log.error("infra.model_pull_failed", engine=engine, model=model_name, error=error)
                raise Exception(f"Failed to pull model: {error}")
            
            log.info("infra.model_pull_success", engine=engine, model=model_name)
            return True
        
        raise Exception(f"Pulling models for {engine} is not supported yet.")

    async def get_installed_models(self, engine: str) -> List[str]:
        """List models currently downloaded and available on this node."""
        if engine == "ollama":
            if not shutil.which("ollama"):
                return []
            try:
                # ollama list output format: NAME  ID  SIZE  MODIFIED
                process = await asyncio.create_subprocess_exec(
                    "ollama", "list",
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE
                )
                stdout, _ = await process.communicate()
                lines = stdout.decode().strip().split("\n")
                if len(lines) <= 1: return [] # Header only or empty
                
                # Skip header, take first column (name)
                # Split by multiple spaces and take the first part
                return [line.split()[0] for line in lines[1:] if line.strip()]
            except Exception as e:
                log.warning("infra.model_list_failed", engine=engine, error=str(e))
                return []
        return []

    async def start_engine(self, name: str):
        """Start a specific LLM engine."""
        if name == "ollama":
            if not shutil.which("ollama"):
                raise Exception("Ollama not installed in PATH")
            # Start in background
            process = await asyncio.create_subprocess_exec(
                "ollama", "serve",
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            log.info("infra.engine_started", engine=name)
            return True
        
        elif name == "llama.cpp":
            from core.collaboration.presence import presence_manager
            
            # 1. Discover all RPC workers in the mesh
            rpc_hosts = []
            for conv_state in presence_manager.presence_state.values():
                for user_state in conv_state.values():
                    if user_state.get("type") == "compute_node":
                        caps = user_state.get("capabilities", {})
                        if caps.get("is_rpc_worker") and caps.get("rpc_endpoint"):
                            rpc_hosts.append(caps["rpc_endpoint"])
            
            # 2. Construct the --rpc flag (comma-separated list)
            rpc_flag = ",".join(rpc_hosts)
            
            # 3. Start llama-server as Master
            cmd = ["llama-server", "--model", "models/default.gguf"] # Placeholder model
            if rpc_flag:
                log.info("infra.distributed_inference_active", hosts=rpc_hosts)
                cmd.extend(["--rpc", rpc_flag])
            
            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            log.info("infra.engine_started", engine=name, distributed=bool(rpc_flag))
            return True

        raise Exception(f"Start logic for {name} not implemented yet")

    async def stop_engine(self, name: str):
        """Stop a specific LLM engine by killing its processes."""
        count = 0
        for proc in psutil.process_iter(['name']):
            if name in proc.info['name'].lower():
                proc.terminate()
                count += 1
        log.info("infra.engine_stopped", engine=name, killed_count=count)
        return count > 0

    def get_system_vram(self) -> float:
        """
        Estimate available VRAM in GB using nvidia-smi.
        """
        try:
            import subprocess
            result = subprocess.run(
                ["nvidia-smi", "--query-gpu=memory.total", "--format=csv,noheader,nounits"],
                capture_output=True, text=True, check=True
            )
            # result might have multiple GPUs, we take the first one
            total_mib = float(result.stdout.strip().split("\n")[0])
            return round(total_mib / 1024, 1)
        except Exception as e:
            log.warning("infra.vram_detection_failed", error=str(e))
            return 0.0 # Unknown

    def get_system_metrics(self) -> Dict[str, Any]:
        """Gather real-time CPU and RAM metrics."""
        ram = psutil.virtual_memory()
        return {
            "vram_gb": self.get_system_vram(),
            "ram_total_gb": round(ram.total / (1024 ** 3), 1),
            "ram_used_gb": round(ram.used / (1024 ** 3), 1),
            "ram_percent": ram.percent,
            "cpu_percent": psutil.cpu_percent(interval=0.1)
        }

    def _is_process_running(self, name: str) -> bool:
        """Check if any process matching the name is active."""
        for proc in psutil.process_iter(['name']):
            try:
                if name.lower() in proc.info['name'].lower():
                    return True
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                pass
        return False

    async def _get_version(self, name: str) -> str:
        """Attempt to get engine version via CLI."""
        try:
            if name == "ollama":
                proc = await asyncio.create_subprocess_exec(
                    "ollama", "--version",
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE
                )
                stdout, _ = await proc.communicate()
                return stdout.decode().strip()
        except:
            pass
        return "unknown"

infrastructure_manager = InfrastructureManager()
