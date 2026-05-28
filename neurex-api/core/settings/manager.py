"""
core/settings/manager.py
Manages dynamic platform configurations.
Settings are hot-reloadable and stored in a persistent JSON registry.
"""

import json
import os
from pathlib import Path
from typing import Any

DEFAULT_SETTINGS = {
    # Agent Models (Default assignments)
    "planner_model": "qwen2.5-coder:14b",
    "coder_model": "qwen2.5-coder:14b",
    "researcher_model": "qwen2.5-coder:14b",
    "reviewer_model": "qwen2.5-coder:14b",
    "tester_model": "qwen2.5-coder:14b",
    # Model Routing (Phase 60: Cognitive Orchestration)
    "model_routes": {
        "Planning": "deepseek-r1:32b",
        "Coding": "qwen2.5-coder:32b",
        "Testing": "qwen2.5-coder:14b",
        "Researching": "qwen2.5-coder:14b",
        "Reviewing": "qwen2.5-coder:14b",
        "Vision": "llama3.2-vision:11b",
        "Media": "llama3.2-vision:11b",
        "Audio": "whisper-large-v3-turbo",
        "Chat": "qwen2.5-coder:14b",
    },
    # Agent Behavior
    "autonomy_level": "limited",
    "enable_agent_internet": False,
    "system_prompt_addition": "",
    # Mesh & Infrastructure
    "enable_mesh_routing": True,
    "enable_distributed_pooling": False,
    "ollama_base_url": "http://localhost:11434",
    # Network Ports
    "api_port": 8000,
    "web_port": 3000,
    "chromadb_port": 8001,
    "ollama_port": 11434,
    "vllm_port": 8002,
    "llama_cpp_port": 8080,
    "rpc_port": 50051,
    "listen_address": "0.0.0.0",
    "fqdn": "",
    "enable_https": True,
    "ssl_cert_path": "",
    "ssl_key_path": "",
    # Firewall
    "firewall_enabled": True,
    "firewall_lan_only": True,
    # Security & Filesystem
    "neurex_trash_path": ".neurex/trash",
    "enable_push_notifications": True,
    # Appearance
    "enable_glassmorphism": True,
    "enable_animations": True,
    "theme_preset": "obsidian",
    "accent_color": "#9c6fff",
    "glow_color": "#9c6fff66",
    "enable_swarm_glow": True,
    # LLM Advanced
    "llm_temperature": 0.7,
    "llm_context_length": 8192,
    # Workspace
    "auto_save_files": True,
    "show_hidden_files": False,
    # System Lifecycle
    "enable_insomnia": True,
    # Storage & Paths
    "neurex_install_dir": str(Path.home() / ".neurex"),
    "models_dir": str(Path.home() / ".ollama" / "models"),
    "storage_paths": [str(Path.home())],  # Primary storage paths for disk telemetry
    "validate_path_permissions": True,
    # UI Layout
    "menu_mode": "horizontal",
    "terminal_line_height": 1.2,
    "terminal_font_size": 13,
    "terminal_font_family": "'JetBrains Mono', 'Fira Code', monospace",
    "terminal_cursor_style": "block",
    # Gitea Actions
    "gitea_base_url": "http://localhost:3000",
    "gitea_token": "",
    "gitea_owner": "",
    "gitea_repo": "",
}


class SettingsManager:
    def __init__(self):
        self.global_settings: dict[str, Any] = {}
        self.workspace_settings: dict[str, Any] = {}
        self._load_global()
        self._load_workspace()

    def _get_global_path(self) -> Path:
        return Path.home() / ".neurex_settings.json"

    def _get_workspace_path(self) -> Path | None:
        ws = os.getenv("WORKSPACE_PATH")
        if ws:
            return Path(ws) / ".neurex" / "settings.json"
        return None

    def _load_global(self):
        path = self._get_global_path()
        if path.exists():
            try:
                with open(path) as f:
                    self.global_settings = json.load(f)
            except Exception:
                self.global_settings = {}
        else:
            self.global_settings = {}
            # Initialize with empty dict to save
            self._save_global()

    def _load_workspace(self):
        path = self._get_workspace_path()
        if path and path.exists():
            try:
                with open(path) as f:
                    self.workspace_settings = json.load(f)
            except Exception:
                self.workspace_settings = {}
        else:
            self.workspace_settings = {}

    def _save_global(self):
        path = self._get_global_path()
        path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, "w") as f:
            json.dump(self.global_settings, f, indent=2)

    def _save_workspace(self):
        path = self._get_workspace_path()
        if path:
            path.parent.mkdir(parents=True, exist_ok=True)
            with open(path, "w") as f:
                json.dump(self.workspace_settings, f, indent=2)

    def reload(self):
        self._load_global()
        self._load_workspace()

    def get_all(self) -> dict[str, Any]:
        # Merge hierarchy: Default -> Global -> Workspace
        merged = DEFAULT_SETTINGS.copy()
        merged.update(self.global_settings)
        merged.update(self.workspace_settings)
        return merged

    def get(self, key: str) -> Any:
        # Check env first for high-priority overrides
        env_val = os.getenv(key.upper())
        if env_val is not None:
            return env_val

        # Then Workspace -> Global -> Default
        if key in self.workspace_settings:
            return self.workspace_settings[key]
        if key in self.global_settings:
            return self.global_settings[key]
        return DEFAULT_SETTINGS.get(key)

    def update(self, key: str, value: Any, scope: str = "global") -> bool:
        """Update a setting in the specified scope ('global' or 'workspace')."""
        if scope == "workspace":
            self.workspace_settings[key] = value
            self._save_workspace()
            return True
        else:
            self.global_settings[key] = value
            self._save_global()
            return True


settings_manager = SettingsManager()
