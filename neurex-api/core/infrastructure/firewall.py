"""
core/infrastructure/firewall.py
Cross-platform firewall manager for Neurex.

Manages port rules on Linux (ufw/iptables), macOS (pf), and Windows (netsh).
Rules are tagged "neurex" for clean tracking and removal when ports change.

Port ownership philosophy:
  - Rules are bound to the specific interface/IP selected at install time.
  - On Windows, rules are bound to the docker.exe process.
  - On Linux/macOS, Docker manages iptables internally; we use ufw/pf to
    control *which sources* can reach Neurex ports (LAN-only by default).
  - When a user changes ports in Settings, old rules are removed and new
    ones are applied atomically.
"""

from __future__ import annotations

import asyncio
import os
import platform
import socket
from dataclasses import dataclass, field

import structlog

log = structlog.get_logger()

NEUREX_TAG = "neurex"  # Used to identify and clean our rules across platforms


@dataclass
class PortSet:
    """Describes the set of ports Neurex needs open for a given role."""

    # port → description
    ports: dict[int, str] = field(default_factory=dict)
    # Source CIDR allowed to reach these ports ("0.0.0.0/0" = any)
    allow_from: str = "0.0.0.0/0"
    # Protocol
    proto: str = "tcp"


def get_master_ports(
    api_port: int = 8000,
    web_port: int = 3000,
    chromadb_port: int = 8001,
    ollama_port: int = 11434,
) -> PortSet:
    return PortSet(
        ports={
            api_port: "Neurex API (FastAPI)",
            web_port: "Neurex Web UI",
            chromadb_port: "ChromaDB (Hive Mind)",
            ollama_port: "Ollama inference server",
            80: "HTTP (Caddy)",
            443: "HTTPS (Caddy)",
        }
    )


def get_node_ports(rpc_port: int = 50051) -> PortSet:
    return PortSet(
        ports={
            rpc_port: "llama-rpc-server (tensor offload)",
        }
    )


def _local_subnet(bind_ip: str) -> str:
    """
    Derive the /24 LAN subnet from a given IP.
    e.g. '192.168.1.42' → '192.168.1.0/24'
    Falls back to '0.0.0.0/0' on failure.
    """
    try:
        parts = bind_ip.split(".")
        if len(parts) == 4:
            return f"{parts[0]}.{parts[1]}.{parts[2]}.0/24"
    except Exception:
        pass
    return "0.0.0.0/0"


# ──────────────────────────────────────────────────────────────────────────────
# Linux — ufw
# ──────────────────────────────────────────────────────────────────────────────


async def _ufw_available() -> bool:
    try:
        r = await asyncio.create_subprocess_exec(
            "ufw", "version", stdout=asyncio.subprocess.DEVNULL, stderr=asyncio.subprocess.DEVNULL
        )
        await r.communicate()
        return r.returncode == 0
    except FileNotFoundError:
        return False


async def _run(cmd: list[str]) -> tuple[int, str]:
    proc = await asyncio.create_subprocess_exec(
        *cmd,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.STDOUT,
    )
    out, _ = await proc.communicate()
    return proc.returncode, out.decode(errors="replace").strip()


async def _linux_remove_rules() -> None:
    """Delete all ufw rules that contain our tag comment."""
    # ufw doesn't have a native tag system; we embed the tag in the comment
    # and use `ufw status numbered` to find and delete matching rules.
    rc, output = await _run(["ufw", "status", "numbered"])
    if rc != 0:
        return

    # Collect rule numbers that mention our tag (reverse order for safe deletion)
    rule_nums: list[int] = []
    for line in output.splitlines():
        if NEUREX_TAG in line.lower():
            # Lines look like: [ 3] 8000/tcp   ALLOW IN    Anywhere   # neurex
            try:
                num = int(line.split("]")[0].strip().lstrip("["))
                rule_nums.append(num)
            except (ValueError, IndexError):
                pass

    for num in sorted(rule_nums, reverse=True):
        await _run(["ufw", "--force", "delete", str(num)])
        log.info("firewall.ufw_rule_deleted", num=num)


async def _linux_apply(port_set: PortSet, bind_ip: str) -> list[str]:
    """
    Apply ufw rules. If bind_ip is not 0.0.0.0, restrict to that interface.
    Returns list of applied rule descriptions for logging.
    """
    if not await _ufw_available():
        log.warning("firewall.ufw_not_found", hint="Install ufw: sudo apt install ufw")
        return []

    await _linux_remove_rules()

    applied = []
    source = port_set.allow_from if bind_ip == "0.0.0.0" else _local_subnet(bind_ip)

    for port, desc in port_set.ports.items():
        # Allow from source subnet to this port; append tag as comment
        cmd = [
            "ufw",
            "allow",
            "from",
            source,
            "to",
            "any",
            "port",
            str(port),
            "proto",
            port_set.proto,
            "comment",
            f"{NEUREX_TAG}: {desc}",
        ]
        rc, out = await _run(cmd)
        if rc == 0:
            log.info("firewall.ufw_rule_added", port=port, source=source, desc=desc)
            applied.append(f"ufw allow {source}→{port}/{port_set.proto} ({desc})")
        else:
            log.error("firewall.ufw_error", port=port, error=out)

    # Ensure ufw is enabled
    await _run(["ufw", "--force", "enable"])
    return applied


# ──────────────────────────────────────────────────────────────────────────────
# macOS — pf (Packet Filter)
# ──────────────────────────────────────────────────────────────────────────────

PF_ANCHOR_FILE = "/etc/pf.anchors/neurex"
PF_CONF_FILE = "/etc/pf.conf"
PF_ANCHOR_REF = f'anchor "{NEUREX_TAG}"'
PF_LOAD_REF = f'load anchor "{NEUREX_TAG}" from "{PF_ANCHOR_FILE}"'


async def _macos_remove_rules() -> None:
    """Flush the Neurex pf anchor."""
    await _run(["pfctl", "-a", NEUREX_TAG, "-F", "rules"])
    log.info("firewall.pf_anchor_flushed")


async def _macos_apply(port_set: PortSet, bind_ip: str) -> list[str]:
    """Write a pf anchor file and load it."""
    source = (
        "any"
        if port_set.allow_from == "0.0.0.0/0" or bind_ip == "0.0.0.0"
        else _local_subnet(bind_ip)
    )
    src_expr = "any" if source == "any" else f"from {source}"

    rules = [
        "# Neurex firewall rules — auto-generated by neurex installer",
        "# DO NOT edit manually. Use Neurex Settings to change ports.",
    ]
    for port, desc in port_set.ports.items():
        rules.append(f"pass in quick proto tcp {src_expr} to any port {port}  # {desc}")

    anchor_content = "\n".join(rules) + "\n"

    try:
        with open(PF_ANCHOR_FILE, "w") as f:
            f.write(anchor_content)
    except PermissionError:
        log.error("firewall.pf_permission_denied", hint="Run installer with sudo")
        return []

    # Ensure anchor is referenced in pf.conf
    try:
        conf = open(PF_CONF_FILE).read() if os.path.exists(PF_CONF_FILE) else ""
        if PF_ANCHOR_REF not in conf:
            with open(PF_CONF_FILE, "a") as f:
                f.write(f"\n{PF_ANCHOR_REF}\n{PF_LOAD_REF}\n")
    except PermissionError:
        pass

    await _run(["pfctl", "-a", NEUREX_TAG, "-f", PF_ANCHOR_FILE])
    await _run(["pfctl", "-e"])  # ensure pf is enabled
    log.info("firewall.pf_anchor_loaded", ports=list(port_set.ports.keys()))
    return [f"pf pass in tcp {source}→{p} ({d})" for p, d in port_set.ports.items()]


# ──────────────────────────────────────────────────────────────────────────────
# Windows — netsh advfirewall
# ──────────────────────────────────────────────────────────────────────────────

DOCKER_PATHS = [
    r"C:\Program Files\Docker\Docker\resources\bin\docker.exe",
    r"C:\Program Files\Docker Desktop\Docker Desktop.exe",
]


def _find_docker_exe() -> str | None:
    for p in DOCKER_PATHS:
        if os.path.exists(p):
            return p
    return None


async def _windows_remove_rules() -> None:
    """Delete all firewall rules with our tag name prefix."""
    await _run(["netsh", "advfirewall", "firewall", "delete", "rule", f"name={NEUREX_TAG}"])
    log.info("firewall.netsh_rules_deleted")


async def _windows_apply(port_set: PortSet, bind_ip: str) -> list[str]:
    """Add Windows Firewall rules using netsh, bound to docker.exe where possible."""
    await _windows_remove_rules()

    docker_exe = _find_docker_exe()
    applied = []

    for port, desc in port_set.ports.items():
        rule_name = f"{NEUREX_TAG} — {desc} ({port})"
        cmd = [
            "netsh",
            "advfirewall",
            "firewall",
            "add",
            "rule",
            f"name={rule_name}",
            "dir=in",
            "action=allow",
            f"protocol={port_set.proto}",
            f"localport={port}",
            "enable=yes",
        ]
        # Bind to specific local IP if not binding to all interfaces
        if bind_ip and bind_ip != "0.0.0.0":
            cmd += [f"localip={bind_ip}"]

        # Restrict remote source if LAN-only binding
        if port_set.allow_from != "0.0.0.0/0":
            cmd += [f"remoteip={port_set.allow_from}"]

        # Process binding — attach to docker.exe if found
        if docker_exe:
            cmd += [f"program={docker_exe}"]

        rc, out = await _run(cmd)
        if rc == 0:
            log.info("firewall.netsh_rule_added", port=port, desc=desc)
            applied.append(f"netsh allow in tcp→{port} ({desc})")
        else:
            log.error("firewall.netsh_error", port=port, error=out)

    return applied


# ──────────────────────────────────────────────────────────────────────────────
# Public API
# ──────────────────────────────────────────────────────────────────────────────


class FirewallManager:
    """
    Cross-platform firewall manager.
    Call apply_rules() at install time and whenever ports change in Settings.
    """

    def __init__(self):
        self._system = platform.system().lower()  # 'linux', 'darwin', 'windows'

    @property
    def platform_name(self) -> str:
        return {"linux": "Linux/ufw", "darwin": "macOS/pf", "windows": "Windows/netsh"}.get(
            self._system, f"Unknown ({self._system})"
        )

    async def apply_rules(
        self,
        role: str,
        bind_ip: str = "0.0.0.0",
        api_port: int = 8000,
        web_port: int = 3000,
        chromadb_port: int = 8001,
        ollama_port: int = 11434,
        rpc_port: int = 50051,
        lan_only: bool = True,
    ) -> dict:
        """
        (Re-)apply firewall rules for the given Neurex role.
        Safe to call multiple times — always removes old rules first.
        """
        if role == "master":
            port_set = get_master_ports(api_port, web_port, chromadb_port, ollama_port)
        else:
            port_set = get_node_ports(rpc_port)

        if lan_only and bind_ip != "0.0.0.0":
            port_set.allow_from = _local_subnet(bind_ip)
        elif lan_only:
            # Try to auto-detect LAN subnet
            try:
                s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
                s.connect(("8.8.8.8", 80))
                detected_ip = s.getsockname()[0]
                s.close()
                port_set.allow_from = _local_subnet(detected_ip)
            except Exception:
                pass

        log.info(
            "firewall.applying",
            platform=self.platform_name,
            role=role,
            ports=list(port_set.ports.keys()),
            allow_from=port_set.allow_from,
        )

        if self._system == "linux":
            applied = await _linux_apply(port_set, bind_ip)
        elif self._system == "darwin":
            applied = await _macos_apply(port_set, bind_ip)
        elif self._system == "windows":
            applied = await _windows_apply(port_set, bind_ip)
        else:
            log.warning("firewall.unsupported_platform", system=self._system)
            applied = []

        return {
            "platform": self.platform_name,
            "role": role,
            "rules_applied": applied,
            "ports": list(port_set.ports.keys()),
            "allow_from": port_set.allow_from,
        }

    async def check_integrity(self, role: str, bind_ip: str, port_set: PortSet) -> bool:
        """Verify if all expected rules are present in the system firewall."""
        if self._system == "linux":
            return await self._linux_check(port_set, bind_ip)
        elif self._system == "darwin":
            return await self._macos_check(port_set, bind_ip)
        elif self._system == "windows":
            return await self._windows_check(port_set, bind_ip)
        return True

    async def _linux_check(self, port_set: PortSet, bind_ip: str) -> bool:
        rc, output = await _run(["ufw", "status"])
        if rc != 0:
            return False
        source = port_set.allow_from if bind_ip == "0.0.0.0" else _local_subnet(bind_ip)
        for port in port_set.ports:
            if f"{port}/{port_set.proto}" not in output or source not in output:
                return False
        return True

    async def _macos_check(self, port_set: PortSet, bind_ip: str) -> bool:
        rc, output = await _run(["pfctl", "-a", NEUREX_TAG, "-s", "rules"])
        if rc != 0:
            return False
        for port in port_set.ports:
            if f"port {port}" not in output:
                return False
        return True

    async def _windows_check(self, port_set: PortSet, bind_ip: str) -> bool:
        rc, output = await _run(["netsh", "advfirewall", "firewall", "show", "rule", "name=all"])
        if rc != 0:
            return False
        for port in port_set.ports:
            if f"({port})" not in output or NEUREX_TAG not in output:
                return False
        return True

    async def start_sentinel(self, interval_hours: int = 1):
        """Background task to periodically verify and heal firewall rules."""
        from core.settings.manager import settings_manager

        log.info("firewall.sentinel_started", interval_hours=interval_hours)

        while True:
            await asyncio.sleep(interval_hours * 3600)
            if not settings_manager.get("firewall_enabled"):
                continue

            role = os.getenv("NODE_ROLE", "master")
            bind_ip = os.getenv("BIND_IP", "0.0.0.0")

            # Fetch expected ports
            if role == "master":
                ports = get_master_ports(
                    settings_manager.get("api_port"),
                    settings_manager.get("web_port"),
                    settings_manager.get("chromadb_port"),
                    settings_manager.get("ollama_port"),
                )
            else:
                ports = get_node_ports(settings_manager.get("rpc_port"))

            if not await self.check_integrity(role, bind_ip, ports):
                log.warning(
                    "firewall.integrity_failure", reason="Rules tampered or missing. Healing..."
                )
                await self.apply_rules(
                    role=role,
                    bind_ip=bind_ip,
                    api_port=settings_manager.get("api_port"),
                    web_port=settings_manager.get("web_port"),
                    chromadb_port=settings_manager.get("chromadb_port"),
                    ollama_port=settings_manager.get("ollama_port"),
                    rpc_port=settings_manager.get("rpc_port"),
                    lan_only=settings_manager.get("firewall_lan_only"),
                )

    async def check_startup(self):
        """Verify firewall on startup. If missing, apply immediately."""
        from core.settings.manager import settings_manager

        if not settings_manager.get("firewall_enabled"):
            return

        role = os.getenv("NODE_ROLE", "master")
        bind_ip = os.getenv("BIND_IP", "0.0.0.0")

        # Apply immediately to be safe on startup
        await self.apply_rules(
            role=role,
            bind_ip=bind_ip,
            api_port=settings_manager.get("api_port"),
            web_port=settings_manager.get("web_port"),
            chromadb_port=settings_manager.get("chromadb_port"),
            ollama_port=settings_manager.get("ollama_port"),
            rpc_port=settings_manager.get("rpc_port"),
            lan_only=settings_manager.get("firewall_lan_only"),
        )
        log.info("firewall.startup_check_complete")


# Singleton
firewall_manager = FirewallManager()
