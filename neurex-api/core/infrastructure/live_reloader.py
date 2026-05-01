"""
core/infrastructure/live_reloader.py
Phase 45: Sentient IDE (Runtime Evolution)
Enables zero-restart logic reloading for core Neurex modules.
Allows the Mesh to update its own soul without terminating the process.
\"\"\"
import sys
import importlib
import structlog
from typing import Optional

log = structlog.get_logger()

class LiveReloader:
    def __init__(self):
        self.registry = {} # module_name -> module_object

    def reload_module(self, file_path: str) -> bool:
        \"\"\"
        Converts a file path to a module name and reloads it in-place.
        Example: 'core/agents/coder_agent.py' -> 'core.agents.coder_agent'
        \"\"\"
        try:
            if not file_path.endswith(".py"):
                return False
                
            # Normalize path to module name
            module_name = file_path.replace(".py", "").replace("/", ".")
            # Handle neurex-api prefix if present in absolute paths
            if "neurex-api." in module_name:
                module_name = module_name.split("neurex-api.")[-1]
            
            if module_name in sys.modules:
                log.info("runtime.reloading_module", module=module_name)
                importlib.reload(sys.modules[module_name])
                return True
            else:
                log.warning("runtime.module_not_found", module=module_name)
                # Try to import it if it's new
                try:
                    importlib.import_module(module_name)
                    return True
                except:
                    return False
        except Exception as e:
            log.error("runtime.reload_failure", module=file_path, error=str(e))
            return False

    def hot_swap_class(self, module_name: str, class_name: str):
        \"\"\"
        EXPERIMENTAL: Swaps class definitions in memory.
        Best used for Stateless Logic or Agent Templates.
        \"\"\"
        # TODO: Implement deep class swapping for long-lived agent instances
        pass

live_reloader = LiveReloader()
