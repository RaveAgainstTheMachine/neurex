# ⬡ Neurex — Federated Agentic IDE

> **Reclaim your hardware. Reclaim your intelligence.**

Neurex is the first decentralized AI operating system designed to run **massive, open-source models on consumer hardware**. Whether deployed as a **Standalone Master** on a single workstation or a **Federated Swarm** across multiple rigs, Neurex delivers enterprise-grade agentic power without the "Cloud Tax" or privacy compromises of centralized providers.

---

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    NEUREX MASTER NODE                       │
│                                                             │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────────┐   │
│  │  neurex-web  │  │  neurex-api  │  │   ChromaDB       │   │
│  │  Vite+React  │  │  (FastAPI)   │  │  (Hive Mind)     │   │
│  │  Monaco+Xterm│  │  WebSocket   │  │  Vector Store    │   │
│  └──────────────┘  └──────┬───────┘  └──────────────────┘   │ 
│                           │                                 │
│              ┌────────────┼────────────┐                    │
│              ▼            ▼            ▼                    │
│         Orchestrator   MeshRouter   MemoryWorker            │
│         (Agents)       (Load Bal)   (File Watcher)          │
└─────────────────────────────────────────────────────────────┘
                    │              │
         ┌──────────┘              └──────────┐
         ▼                                    ▼
┌─────────────────┐                ┌─────────────────┐
│  RPC NODE A     │                │  RPC NODE B     │
│  llama-rpc-svr  │  ◄─ VRAM ─►    │  llama-rpc-svr  │
│  heartbeat agent│                │  heartbeat agent│
└─────────────────┘                └─────────────────┘
```

| Layer | Technology |
|:---|:---|
| **Frontend** | Vite + React + TypeScript + Monaco Editor + Xterm.js |
| **Backend API** | FastAPI + SQLModel + aiosqlite (SQLite) |
| **Agent Orchestration** | Custom multi-agent graph (Planner, Coder, Reviewer, Tester, Researcher, Summarizer) |
| **Inference** | llama.cpp (via Ollama) + Distributed RPC for mesh inference |
| **Collective Memory** | ChromaDB + sentence-transformers + Tree-Sitter chunking |
| **Terminal Sandbox** | Docker (neurex-sandbox image) — RO workspace, network-none, 512MB/1CPU cap |
| **MCP Toolset** | Filesystem, Terminal, Browser (Playwright), Web Search |
| **Security** | JWT (HS256, 24h) + bcrypt + RBAC (Admin/Developer/Viewer) |
| **Real-time** | WebSocket (presence, streaming tokens, terminal I/O, HITL approvals) |
| **Proxy/SSL** | Caddy (automatic Let's Encrypt) |

---

## Quick Start

### Option 1: Interactive Installer (Recommended)

```bash
git clone https://git.mcfrosty.com/frosty/neurex.git
cd neurex
bash install.sh
```

The installer will ask whether you're setting up a **Master** (full stack) or a **Node** (RPC GPU worker), then walk you through all configuration options.

### Option 2: Docker Compose (Master)

```bash
cp .env.example .env   # fill in JWT_SECRET, ADMIN_OTP etc.
docker-compose up -d
```

Visit `http://localhost:3000` → complete onboarding with your Admin OTP.

### Option 3: Adding a Node to an existing Master

On the Node machine:
```bash
git clone https://git.mcfrosty.com/frosty/neurex.git
cd neurex
bash install.sh   # select "Node" when prompted
docker-compose -f docker-compose.node.yml up -d
```

The Node registers with the Master automatically via the heartbeat agent and appears in the Infrastructure Dashboard within 15 seconds.

---

## Key Features

### 🧠 Federated Compute Mesh
*   **Consumer-Grade Sovereignty**: Built specifically to run state-of-the-art Open Source models (Qwen2.5-Coder, DeepSeek-R1) on the hardware you already own.
*   **Standalone or Federated**: Run as a complete sovereign cell on a single machine, or scale horizontally by pooling VRAM, GPU shaders, and CPU cycles across a local compute mesh.
*   **Pocket-Orchestration (Mobile)**: Not limited to your desk. Oversee agent pipelines, start new projects, and issue human-in-the-loop approvals via **Voice & Text** from any mobile device.
*   **Full-Spectrum Pooling**: Aggregates every available resource—VRAM, RAM, and Compute (CPU/GPU)—into a unified, high-performance inference engine.
- **Weighted-Load MeshRouter**: routes inference to the node with the best capability score (`VRAM × 2 / (CPU + latency/10 + queue×20 + 1)`)
- Swarm heartbeat every 15 seconds — automatic peer discovery

### ⬡ Hive Mind (Collective Memory)
- Every file save is semantically indexed (< 150ms) into ChromaDB
- Tree-Sitter code-aware chunking preserves function and class boundaries
- Semantic search returns relevant code fragments with relevance scores
- The entire swarm shares one collective knowledge base

### 🤖 Multi-Agent Orchestration
- **Planner** → **Coder** → **Reviewer** → **Tester** pipeline
- SQLite-backed Task Graph — resumable after interrupts
- Staleness detection prevents infinite loops (iteration cap + tool-call deduplication)

### 🛡️ Zero-Trust Security
- **HITL Approval Gates**: every terminal command above the autonomy ceiling requires explicit human sign-off
- **One-Way Trash**: agents move files to `.neurex/trash`, never permanently delete
- **Cross-Platform Firewall**: Atomic protection for Neurex ports on Linux (ufw), macOS (pf), and Windows (netsh).
- **LAN-Only Restriction**: Optional one-click lockdown to prevent external exposure.
- **Path Traversal Shield**: all filesystem ops are validated against `WORKSPACE_PATH`
- **Sandbox Isolation**: Docker container, read-only workspace mount, no network by default
- **RBAC**: Admin / Developer / Viewer with role hierarchy enforced on every endpoint
- **Autonomy Ceiling**: system-wide maximum set at install; per-chat level can be lower, never higher

### 👥 Real-Time Collaboration
- WebSocket presence broadcasting (cursors, file locks, status)
- Collaboration file locking prevents agent/human write conflicts
- **Mobile Command & Voice**: Integrated Web Speech API for hands-free dictation and text-to-speech (TTS) playback of agent responses.

### 🔄 Self-Update
- Polls GitHub Releases every 30 minutes
- Downloads new Docker images in the background (`docker compose pull`)
- Pulsing badge in status bar → popover with version diff → "Restart to update" on completion

---

## Project Structure

```
neurex/
├── install.sh                  # Bootstrap installer (creates ephemeral venv)
├── install.py                  # Role-aware interactive installer (Master/Node)
├── docker-compose.yml          # Master: full stack
├── docker-compose.node.yml     # Node: RPC worker + heartbeat only
├── neurex-api/                 # FastAPI backend
│   ├── main.py
│   ├── requirements.txt
│   ├── api/routes/             # auth, chat, tasks, files, infra, memory,
│   │                           # skills, settings, notifications, update
│   ├── api/websocket.py        # WS handler (streaming, terminal, presence)
│   └── core/
│       ├── agents/             # Planner, Coder, Reviewer, Tester, Researcher, Summarizer
│       ├── collaboration/      # presence.py, manager.py
│       ├── context/            # rules_parser.py (.neurexrules)
│       ├── infrastructure/     # manager.py, mesh.py, distributed.py,
│       │                       # benchmarker.py, registry.py, heartbeat_agent.py
│       ├── mcp/                # client.py + tools/ (filesystem, terminal, browser, researcher)
│       ├── memory/             # hive.py, worker.py, chunker.py, embedder.py
│       ├── settings/           # manager.py
│       ├── skills/             # manager.py
│       ├── terminal/           # pty_manager.py
│       ├── orchestrator.py
│       └── task_graph.py       # SQLModel schema + state machine
├── neurex-web/                 # Vite + React frontend
│   └── src/components/         # AIPanel, Editor, FileExplorer, Terminal,
│                               # InfraPanel, HiveMindPanel, SettingsPanel,
│                               # UpdateNotifier, PresenceBar, SkillsPanel, ...
├── API_REFERENCE.md            # Full REST + WebSocket API documentation
├── NEUREX_COMPENDIUM.md        # Deep-dive technical specification
├── NEUREX_MANIFESTO.md         # Multi-lingual feature showcase (EN/FR/AR)
├── HARDWARE_REQUIREMENTS.md    # Minimum and recommended hardware specs
└── .neurexrules                # Agent behavioral guidelines
```

---

## Environment Variables

| Variable | Default | Description |
|:---|:---|:---|
| `NODE_ROLE` | `master` | `master` or `node` |
| `NEUREX_VERSION` | `0.1.0` | Used for update comparisons |
| `WORKSPACE_PATH` | `/workspace` | Root for all agent file operations |
| `LLM_MODELS_PATH` | `./.models` | Local model storage |
| `JWT_SECRET` | *(generated)* | HS256 signing key |
| `ADMIN_OTP` | *(generated)* | One-time onboarding password |
| `AUTONOMY_CEILING` | `limited` | Max agent autonomy: `restricted`, `limited`, `full` |
| `ENABLE_AGENT_INTERNET` | `false` | Allow browser/search tools to reach the web |
| `DEFAULT_MODEL` | `qwen2.5-coder:14b` | Default inference model |
| `NEUREX_GITHUB_REPO` | `TBD/neurex` | Repo for update checks |
| `MASTER_URL` | — | *(Node only)* Master API URL |
| `RPC_PORT` | `50051` | *(Node only)* llama-rpc-server port |

---

## Documentation

| Document | Description |
|:---|:---|
| [`API_REFERENCE.md`](API_REFERENCE.md) | Complete REST & WebSocket API reference |
| [`NEUREX_COMPENDIUM.md`](NEUREX_COMPENDIUM.md) | Technical deep-dive: all subsystems with diagrams |
| [`NEUREX_MANIFESTO.md`](NEUREX_MANIFESTO.md) | Feature showcase in EN / FR (Québécois) / AR |
| [`HARDWARE_REQUIREMENTS.md`](HARDWARE_REQUIREMENTS.md) | Hardware specs for Master and Node deployments |
| [`.neurexrules`](.neurexrules) | Agent behavioral guidelines and coding standards |

---

## Roadmap

| Phase | Status | Description |
|:---|:---|:---|
| Phase 1–9 | ✅ Complete | Core IDE, agents, memory, RBAC, collaboration |
| Phase 10.5 | ✅ Complete | Distributed Tensor Pooling (llama.cpp RPC) |
| Phase 11 | ✅ Complete | Hive Mind UI (semantic search portal) |
| Phase 12 | ✅ Complete | RBAC frontend enforcement |
| Phase 13 | ✅ Complete | Role-aware installer, self-update system |
| Phase 13.5| 🔲 In Progress | **BYOK Gateway**: Support for OpenAI, Anthropic, Gemini |
| Phase 14 | 🔲 Planned | LSP integration (diagnostics, hover, go-to-def) |
| Phase 15 | 🔲 Planned | Git UI panel (diff, stage, commit, branch) |
| Phase 16 | 🔲 Planned | DAP Debugger (breakpoints, step-through) |
| Phase 17 | 🔲 Planned | Diagnostics panel + find-across-files |
| Phase 18 | 🔲 Planned | Plugin Marketplace (Skills → Extensions) |

---

*Built with love by **Steven Frost** with the assistance of **Antigravity**, a powerful AI coding assistant. Absolute Autonomy. Federated Intelligence.*
