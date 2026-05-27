"""
core/infrastructure/hot_reload.py
Dynamic module reloading service for Neurex.
"""

from __future__ import annotations

import os

import structlog

from core.agents.registry import reload_agent

log = structlog.get_logger()


class HotReloadManager:
    def handle_file_change(self, path: str):
        """
        Triggered when a file changes. If it's an agent, reload it.
        """
        if "core/agents/" in path and path.endswith(".py"):
            filename = os.path.basename(path)
            if filename == "__init__.py" or filename == "registry.py":
                return

            # Convert path to module name
            # Example: core/agents/coder_agent.py -> core.agents.coder_agent
            agent_name = filename.replace(".py", "")
            if agent_name.endswith("_agent"):
                short_name = agent_name.replace("_agent", "")
                module_name = f"core.agents.{agent_name}"

                log.info("hot_reload.trigger", agent=short_name, module=module_name)
                success = reload_agent(module_name, short_name)
                if success:
                    log.info("hot_reload.success", agent=short_name)
                else:
                    log.error("hot_reload.failed", agent=short_name)


hot_reload_manager = HotReloadManager()
