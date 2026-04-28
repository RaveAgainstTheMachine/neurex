# ⬡ NEUREX — The Agentic Operating System

Neurex is a next-generation development environment designed not just as a code editor, but as a **Distributed Intelligence Mesh**. It aggregates local compute resources into a federated swarm, enabling autonomous agents to plan, execute, and refactor code within a high-trust, observed ecosystem.

## 🧠 Why Neurex?

While traditional AI IDEs (Cursor, Windsurf) act as "Assistants," Neurex acts as a **Hive Mind**. It is built on three core pillars:

1.  **Agentic Autonomy**: A multi-agent orchestrator (Planner, Coder, Researcher) that iterates on tasks in loops, not just one-shot completions.
2.  **Distributed Swarm**: Pool VRAM across your local network to run massive models (32B+) that would normally require a server farm.
3.  **Total Observability**: The **Flight Recorder** streams every reasoning trace and tool-call in real-time. No "Black Box" magic—just transparent intelligence.
4.  **Collective Memory**: A decentralized vector-memory that allows agents to "recall" architectural precedents across projects and sessions.

## Quick Start

### 1. Requirements
- Linux (Ubuntu/Debian/CachyOS recommended)
- Docker + NVIDIA Container Toolkit (for sandbox and local GPU support)
- Python 3.14+
- Node.js 20+

### 2. Installation & Setup

**Linux / macOS:**
```bash
git clone https://github.com/USERNAME/neurex.git
cd neurex
bash install.sh
```

**Windows (Docker Desktop + WSL2):**
Ensure Docker Desktop is running, then run in PowerShell:
```powershell
.\neurex.ps1
```

### 3. Launching the OS

**Linux / macOS:**
```bash
./neurex/neurex.sh
```

**Windows:**
```powershell
.\neurex.ps1
```

## Technical Documentation

| Document | Description |
| :--- | :--- |
| [**Architecture**](ARCHITECTURE.md) | Technical deep-dive into inference pooling, memory, and agents. |
| [**Features**](FEATURES.md) | Comprehensive list of technical capabilities and security specs. |
| [**API Reference**](API_REFERENCE.md) | REST and WebSocket endpoint specifications. |
| [**Hardware Requirements**](HARDWARE_REQUIREMENTS.md) | VRAM and network specs for distributed clusters. |

## Security Policy
- **Authentication**: JWT (HS256) with 8-hour rotation.
- **Encryption**: Salted PBKDF2-SHA256 password hashing.
- **Isolation**: Commands run in restricted Docker containers (no network, read-only mounts).
- **Control**: Mandatory Human-in-the-loop (HITL) approvals for high-autonomy tasks.

## UI Customization
Neurex features a high-fidelity, customizable interface:
- **Dynamic Accent Colors**: Change the platform's visual identity (accents, glows, pulses) in real-time.
- **Glassmorphism**: GPU-accelerated backdrop blurs for a premium, immersive workspace.
- **Motion System**: Smooth kinetic transitions and neural animations (can be toggled for performance).
- **Persistent State**: All theme and layout preferences are saved to the backend node registry.

## License
Neurex is licensed under the **Business Source License 1.1**.

*   **Free for Personal Use**: Anyone can use Neurex for non-commercial projects.
*   **Startup Friendly**: Free for commercial use by companies with less than $5,000,000 USD in annual gross revenue.
*   **Eventual Open Source**: Automatically converts to **Apache License 2.0** on 2030-01-01.

See [LICENSE](LICENSE) for the full legal text.

---
© 2026 Steven Frost. All rights reserved.
