"""
core/agents/registry.py
Central registry for specialized agents. Supports hot-reloading of agent logic.
"""

from __future__ import annotations

import importlib

import structlog

log = structlog.get_logger()

# Global registry of agent classes
AGENT_REGISTRY: dict[str, type] = {}


def register_agent(name: str, agent_class: type):
    AGENT_REGISTRY[name] = agent_class
    log.info("agent.registered", name=name, class_name=agent_class.__name__)


def get_agent_class(name: str) -> type | None:
    return AGENT_REGISTRY.get(name)


def reload_agent(module_name: str, agent_name: str):
    """
    Hot-reloads an agent's module and updates the registry.
    Example: reload_agent("core.agents.coder_agent", "coder")
    """
    try:
        module = importlib.import_module(module_name)
        importlib.reload(module)

        # Determine the class name (usually CamelCase of agent_name + "Agent")
        # Or look for classes in the module that inherit from a base agent (if we have one)
        # For now, we use a mapping or convention.
        class_name = "".join(word.capitalize() for word in agent_name.split("_")) + "Agent"
        agent_class = getattr(module, class_name)

        register_agent(agent_name, agent_class)
        log.info("agent.hot_reloaded", name=agent_name, module=module_name)
        return True
    except Exception as e:
        log.error("agent.reload_failed", name=agent_name, error=str(e))
        return False


# Initial registration
from core.agents.coder_agent import CoderAgent
from core.agents.commander_agent import CommanderAgent
from core.agents.debater_agent import DebaterAgent
from core.agents.dependency_agent import DependencyAgent
from core.agents.planner_agent import PlannerAgent
from core.agents.researcher_agent import ResearcherAgent
from core.agents.reviewer_agent import ReviewerAgent
from core.agents.tester_agent import TesterAgent

register_agent("planner", PlannerAgent)
register_agent("coder", CoderAgent)
register_agent("tester", TesterAgent)
register_agent("researcher", ResearcherAgent)
register_agent("reviewer", ReviewerAgent)
register_agent("debater", DebaterAgent)
register_agent("commander", CommanderAgent)
register_agent("dependency", DependencyAgent)
