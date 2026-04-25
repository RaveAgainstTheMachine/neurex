"""
Neurex Enterprise Installer
Role-aware: handles Master (full stack) and Node (RPC worker) installations.
"""
import os
import sys
import socket
import secrets
import webbrowser
from pathlib import Path
import psutil
import requests
import questionary
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.text import Text
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich import print as rprint

console = Console()


# ──────────────────────────────────────────────────────────────────────────────
# Helpers
# ──────────────────────────────────────────────────────────────────────────────

def get_network_interfaces():
    """Detect all available network interfaces and their IPs."""
    interfaces = []
    for name, addresses in psutil.net_if_addrs().items():
        for addr in addresses:
            if addr.family == socket.AF_INET:
                interfaces.append({
                    "name": name,
                    "ip": addr.address,
                    "display": f"{name} ({addr.address})"
                })
    return interfaces


def get_lan_ip():
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except Exception:
        return "127.0.0.1"


def get_wan_ip():
    try:
        return requests.get("https://api.ipify.org", timeout=3).text
    except Exception:
        return "Unknown"


def pick_bind_ip():
    """Interactive bind-interface picker. Returns chosen IP string."""
    interfaces = get_network_interfaces()
    choices = [iface["display"] for iface in interfaces]
    choices.append("0.0.0.0 (Bind to all interfaces — Default)")

    choice = questionary.select(
        "Which network interface should this node listen on?",
        choices=choices,
        default="0.0.0.0 (Bind to all interfaces — Default)"
    ).ask()

    if "0.0.0.0" in choice:
        return "0.0.0.0"
    return choice.split("(")[1].replace(")", "").strip()


def show_banner():
    banner = """
[bold cyan]
███╗   ██╗███████╗██╗   ██╗██████╗ ███████╗██╗  ██╗
████╗  ██║██╔════╝██║   ██║██╔══██╗██╔════╝╚██╗██╔╝
██╔██╗ ██║█████╗  ██║   ██║██████╔╝█████╗   ╚███╔╝ 
██║╚██╗██║██╔══╝  ██║   ██║██╔══██╗██╔══╝   ██╔██╗ 
██║ ╚████║███████╗╚██████╔╝██║  ██║███████╗██╔╝ ██╗
╚═╝  ╚═══╝╚══════╝ ╚═════╝ ╚═╝  ╚═╝╚══════╝╚═╝  ╚═╝
[/bold cyan]
[bold white]Enterprise Agent Platform — Interactive Installer[/bold white]
    """
    console.print(Panel(banner, border_style="cyan", expand=False))


# ──────────────────────────────────────────────────────────────────────────────
# Role explainer
# ──────────────────────────────────────────────────────────────────────────────

def show_role_explainer():
    table = Table(title="Installation Roles", border_style="cyan", show_lines=True)
    table.add_column("Component", style="bold white")
    table.add_column("Master", justify="center", style="green")
    table.add_column("Node (RPC Worker)", justify="center", style="yellow")

    rows = [
        ("Full API + Web UI",              "✅", "❌"),
        ("Agent Orchestration (Planner, Coder…)", "✅", "❌"),
        ("Hive Mind / ChromaDB",           "✅", "❌"),
        ("JWT Auth + RBAC",                "✅", "❌"),
        ("LLM Model Storage (full)",       "✅", "Optional"),
        ("llama-rpc-server (GPU offload)", "❌", "✅"),
        ("Swarm Heartbeat Agent",          "✅", "✅"),
        ("Docker Sandbox",                 "✅", "❌"),
    ]
    for row in rows:
        table.add_row(*row)

    console.print("\n")
    console.print(table)
    console.print("\n[dim]A Node's sole job is to contribute VRAM to the mesh via RPC.[/dim]\n")


# ──────────────────────────────────────────────────────────────────────────────
# Master installation
# ──────────────────────────────────────────────────────────────────────────────

def install_master():
    console.print("\n[bold cyan]═══ MASTER NODE INSTALLATION ═══[/bold cyan]\n")

    # 1. Paths
    console.print("[bold magenta]1. Storage Paths[/bold magenta]")
    default_path = str(Path.cwd().absolute())
    install_path = questionary.path(
        "Where should Neurex be installed?",
        default=default_path
    ).ask()

    llm_path = questionary.path(
        "Where should LLM models be stored? (Requires significant disk space)",
        default=str(Path(install_path) / ".models")
    ).ask()

    # 2. Network
    console.print("\n[bold magenta]2. Network Binding[/bold magenta]")
    bind_ip = pick_bind_ip()

    # 3. Access / Proxy
    console.print("\n[bold magenta]3. Proxy & Access[/bold magenta]")
    setup_type = questionary.select(
        "How will you access Neurex?",
        choices=[
            "Internal Network Only (LAN IP / Tailscale / Localhost)",
            "External Domain (Automatic Let's Encrypt SSL via Caddy)",
            "Behind Existing Proxy (Nginx / Traefik / Cloudflare Tunnel)",
        ]
    ).ask()

    domain = ""
    use_https = False

    if "External Domain" in setup_type:
        domain = questionary.text(
            "Enter your Fully Qualified Domain Name (e.g. neurex.yourdomain.com):"
        ).ask()
        use_https = True
    elif "Internal" in setup_type:
        use_https = questionary.confirm(
            "Enable mTLS / Self-Signed HTTPS for internal network?"
        ).ask()
        domain = bind_ip if bind_ip != "0.0.0.0" else "localhost"
    else:
        domain = "localhost"

    # 4. Autonomy ceiling
    console.print("\n[bold magenta]4. Agent Autonomy Ceiling[/bold magenta]")
    console.print("[dim]This is a system-wide security cap. Individual chats can set their own level up to this ceiling.[/dim]")
    autonomy = questionary.select(
        "Maximum autonomy level any agent or user can reach on this installation?",
        choices=[
            "restricted — Every command requires human approval (most secure)",
            "limited    — Safe commands run freely; dangerous ones ask first (Recommended)",
            "full       — No approval gates (use only in trusted single-user setups)",
        ],
        default="limited    — Safe commands run freely; dangerous ones ask first (Recommended)"
    ).ask()
    autonomy_ceiling = autonomy.split("—")[0].strip()

    # 5. Internet access
    agent_internet = questionary.confirm(
        "Allow agents to access the internet? (Used for web_search and browser tools)",
        default=False
    ).ask()

    # 6. Generate secrets
    console.print("\n[bold magenta]5. Generating Security Perimeters[/bold magenta]")
    with Progress(SpinnerColumn(), TextColumn("[progress.description]{task.description}"), transient=True) as progress:
        task = progress.add_task("Generating cryptographic material...", total=100)
        otp = secrets.token_urlsafe(16)
        progress.update(task, advance=50)
        jwt_secret = secrets.token_hex(32)
        progress.update(task, advance=50)

    # 7. Write .env
    env_content = f"""# Automatically generated by Neurex Installer — Master Node
NODE_ROLE=master
NEUREX_VERSION=0.1.0
WORKSPACE_PATH={install_path}/workspace
LLM_MODELS_PATH={llm_path}
BIND_IP={bind_ip}
NEUREX_DOMAIN={domain}
ADMIN_OTP={otp}
JWT_SECRET={jwt_secret}
USE_HTTPS={str(use_https).lower()}
# AUTONOMY_CEILING is a hard cap — individual chats set their own level up to this max.
# Per-chat autonomy is controlled via the approval dropdown in the AI Panel.
AUTONOMY_CEILING={autonomy_ceiling}
ENABLE_AGENT_INTERNET={str(agent_internet).lower()}
"""
    Path(".env").write_text(env_content)
    console.print("[green]✔[/green] .env written.")

    # 8. Summary
    lan_ip = get_lan_ip()
    wan_ip = get_wan_ip()
    protocol = "https" if use_https else "http"
    access_url = f"{protocol}://{domain if domain not in ('localhost', '0.0.0.0') else lan_ip}:8080"

    summary = f"""
[bold green]Master Installation Complete![/bold green]

[bold yellow]Network Topology:[/bold yellow]
• [cyan]LAN IP:[/cyan]    {lan_ip}
• [cyan]WAN IP:[/cyan]    {wan_ip}
• [cyan]FQDN:[/cyan]      {domain or 'None'}
• [cyan]Binding:[/cyan]   {bind_ip}:8080

[bold yellow]Storage:[/bold yellow]
• [cyan]App Root:[/cyan]  {install_path}
• [cyan]Models:[/cyan]    {llm_path}

[bold yellow]Agent Config:[/bold yellow]
• [cyan]Autonomy Ceiling:[/cyan] {autonomy_ceiling} [dim](per-chat can be lower, never higher)[/dim]
• [cyan]Internet:[/cyan]         {'Enabled' if agent_internet else 'Disabled (Air-Gapped)'}

[bold red]Security Notice — DO NOT LOSE THIS:[/bold red]
Your Initial Admin Onboarding Password is:
[bold white on red] {otp} [/bold white on red]

[dim]Next Steps:[/dim]
1. Run [bold]docker-compose up -d[/bold] to start services.
2. Navigate to [blue underline]{access_url}/onboarding[/blue underline]
3. Add Node machines by running [bold]install.sh[/bold] on them and selecting [bold]Node[/bold].
"""
    console.print(Panel(summary, title="[bold]Neurex Master Deployment Summary[/bold]", border_style="green"))

    if questionary.confirm("Launch browser to onboarding page now?").ask():
        webbrowser.open(f"{access_url}/onboarding?token={otp}")
        console.print("[dim]Browser launched.[/dim]")


# ──────────────────────────────────────────────────────────────────────────────
# Node installation
# ──────────────────────────────────────────────────────────────────────────────

def install_node():
    console.print("\n[bold yellow]═══ RPC NODE INSTALLATION ═══[/bold yellow]\n")
    console.print("[dim]This machine will contribute its VRAM to the swarm via llama-rpc-server.[/dim]\n")

    # 1. Master URL
    console.print("[bold magenta]1. Master Registration[/bold magenta]")
    master_url = questionary.text(
        "Enter the Master Neurex URL (e.g. http://192.168.1.10:8080):",
        validate=lambda v: True if v.startswith("http") else "Must be a valid URL starting with http:// or https://"
    ).ask()

    master_token = questionary.password(
        "Enter the Master Node API token (issued during Master installation):"
    ).ask()

    # 2. Network binding
    console.print("\n[bold magenta]2. RPC Server Binding[/bold magenta]")
    bind_ip = pick_bind_ip()

    rpc_port = questionary.text(
        "RPC server port?",
        default="50051",
        validate=lambda v: True if v.isdigit() else "Must be a number"
    ).ask()

    # 3. VRAM allocation
    console.print("\n[bold magenta]3. VRAM Allocation[/bold magenta]")
    try:
        import subprocess
        gpu_info = subprocess.check_output(
            ["nvidia-smi", "--query-gpu=name,memory.total", "--format=csv,noheader"],
            timeout=3, text=True
        ).strip()
        console.print(f"[green]✔ GPU Detected:[/green] {gpu_info}")
    except Exception:
        console.print("[yellow]⚠ Could not auto-detect GPU. Continuing manually.[/yellow]")
        gpu_info = "Unknown"

    vram_limit = questionary.text(
        "How many GB of VRAM to allocate to the mesh? (0 = all available)",
        default="0",
        validate=lambda v: True if v.replace(".", "").isdigit() else "Must be a number"
    ).ask()

    # 4. Node name
    console.print("\n[bold magenta]4. Node Identity[/bold magenta]")
    default_name = socket.gethostname()
    node_name = questionary.text(
        "Name for this node in the swarm?",
        default=default_name
    ).ask()

    # 5. Write node .env
    env_content = f"""# Automatically generated by Neurex Installer — RPC Node
NODE_ROLE=node
NODE_NAME={node_name}
MASTER_URL={master_url}
MASTER_TOKEN={master_token}
BIND_IP={bind_ip}
RPC_PORT={rpc_port}
VRAM_LIMIT_GB={vram_limit}
"""
    Path(".env").write_text(env_content)
    console.print("[green]✔[/green] .env written.")

    # 6. Summary
    lan_ip = get_lan_ip()

    summary = f"""
[bold yellow]Node Installation Complete![/bold yellow]

[bold cyan]Node Identity:[/bold cyan]
• [cyan]Name:[/cyan]      {node_name}
• [cyan]LAN IP:[/cyan]    {lan_ip}
• [cyan]RPC Addr:[/cyan]  {lan_ip}:{rpc_port}

[bold cyan]Master Registration:[/bold cyan]
• [cyan]Master:[/cyan]    {master_url}

[bold cyan]VRAM Commitment:[/bold cyan]
• [cyan]GPU:[/cyan]       {gpu_info}
• [cyan]Allocated:[/cyan] {'All available' if vram_limit == '0' else vram_limit + ' GB'}

[dim]Next Steps:[/dim]
1. Run [bold]docker-compose -f docker-compose.node.yml up -d[/bold]
2. The Master will automatically discover this node via the heartbeat broadcast.
3. Check swarm status on the Master's [bold]Infrastructure Dashboard[/bold].
"""
    console.print(Panel(summary, title="[bold]Neurex Node Deployment Summary[/bold]", border_style="yellow"))

    console.print("\n[bold yellow]This node will be live once the RPC server starts. The Master will find it automatically.[/bold yellow]\n")


# ──────────────────────────────────────────────────────────────────────────────
# Entry point
# ──────────────────────────────────────────────────────────────────────────────

def main():
    os.system('clear' if os.name == 'posix' else 'cls')
    show_banner()

    # Role selection — the very first question
    console.print("\n[bold magenta]What are you installing?[/bold magenta]")
    show_role_explainer()

    role = questionary.select(
        "Select installation role:",
        choices=[
            "Master  — Full Neurex stack (API, UI, Hive Mind, Orchestration)",
            "Node    — RPC Worker only (contributes VRAM to an existing Master)",
        ]
    ).ask()

    if role is None:
        console.print("\n[red]Installation aborted.[/red]")
        sys.exit(1)

    if "Master" in role:
        install_master()
    else:
        install_node()

    console.print("\n[bold cyan]Welcome to the Swarm.[/bold cyan] ⬡\n")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        console.print("\n[red]Installation aborted by user.[/red]")
        sys.exit(1)
