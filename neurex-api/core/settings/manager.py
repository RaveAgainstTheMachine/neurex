"""
core/settings/manager.py
Manages dynamic platform configurations.
Settings are hot-reloadable and stored in a persistent JSON registry.
"""
import os
import json
from pathlib import Path
from typing import Dict, Any

SETTINGS_FILE = Path(os.getenv("WORKSPACE_PATH", "/workspace")) / ".neurex" / "settings.json"

DEFAULT_SETTINGS = {
    # Agent Behavior
    "autonomy_level": "limited",
    "enable_agent_internet": False,
    "system_prompt_addition": "",

    # Mesh & Infrastructure
    "enable_mesh_routing": True,
    "enable_distributed_pooling": False,
    "ollama_base_url": "http://localhost:11434",

    # Network Ports (changing these re-applies firewall rules automatically)
    "api_port":        8000,
    "web_port":        3000,
    "chromadb_port":   8001,
    "ollama_port":     11434,
    "rpc_port":        50051,

    # Firewall
    "firewall_enabled": True,
    "firewall_lan_only": True,   # Restrict Neurex ports to LAN subnet only

    # Security & Filesystem
    "neurex_trash_path": ".neurex/trash",
    "enable_push_notifications": True,

    # System Lifecycle
    "enable_insomnia": True,
}

class SettingsManager:
    def __init__(self):
        self.settings = DEFAULT_SETTINGS.copy()
        self._load()

    def _load(self):
        SETTINGS_FILE.parent.mkdir(parents=True, exist_ok=True)
        if SETTINGS_FILE.exists():
            try:
                with open(SETTINGS_FILE, "r") as f:
                    data = json.load(f)
                    # Merge with defaults to ensure new keys are populated
                    for k, v in data.items():
                        if k in self.settings:
                            self.settings[k] = v
            except Exception:
                pass
        self._save()

    def _save(self):
        with open(SETTINGS_FILE, "w") as f:
            json.dump(self.settings, f, indent=2)

    def get_all(self) -> Dict[str, Any]:
        return self.settings

    def get(self, key: str) -> Any:
        # Fallback to env var if needed, but prefer JSON
        env_val = os.getenv(key.upper())
        if env_val is not None and key not in self.settings:
            return env_val
        return self.settings.get(key, DEFAULT_SETTINGS.get(key))

    def update(self, key: str, value: Any) -> bool:
        if key in self.settings:
            self.settings[key] = value
            self._save()
            return True
        return False

settings_manager = SettingsManager()
