<div align="center">
  <img src="./assets/neurex_splash.png" width="100%" alt="Neurex Agentic IDE">
  
  <br />

  <h1>⬡ NEUREX</h1>
  <h3>A local-first AI engineering workspace.</h3>

  <p align="center">
    <b>Run models locally, execute agents safely, and collaborate in real time.</b>
  </p>

  <p>
    <a href="./LICENSE"><img src="https://img.shields.io/badge/License-BSL%201.1-purple.svg?style=for-the-badge" alt="License"></a>
    <a href="#"><img src="https://img.shields.io/badge/Version-v0.11.0-blueviolet.svg?style=for-the-badge" alt="Version"></a>
    <a href="#"><img src="https://img.shields.io/badge/Status-Active%20Development-success.svg?style=for-the-badge" alt="Status"></a>
  </p>

  <p align="center">
    <a href="./INSTALL.md"><b>Installation</b></a> •
    <a href="./wiki/Home.md"><b>Documentation</b></a> •
    <a href="./CHANGELOG.md"><b>Changelog</b></a> •
    <a href="./CREDITS.md"><b>Credits</b></a> •
    <a href="./ROADMAP.md"><b>Roadmap</b></a>
  </p>
</div>

---

## What Is Neurex?

**Neurex** is a local-first AI engineering workspace designed for **Human-Agent Parity**. 

Rather than treating AI as a black box executing background code edits, Neurex models agents as first-class IDE collaborators. They possess active multi-cursor overlays, secure file-locking mechanisms, and real-time human-in-the-loop capability guardrails. Neurex specializes in high-fidelity cooperative tasks—such as security hardening, dependency migrations, and codebase grounding—combining a Monaco-based editor, persistent PTY terminals, and a distributed local inference layer that pools consumer GPUs across a LAN.

---

## Core Features

### 🧠 Agentic Orchestration
*   **Task Graphs**: Persistent SQLite-backed task plans that survive restarts.
*   **Role-Based Routing**: Assign different models to planning, coding, and review tasks independently.
*   **Multi-Agent Review**: Route changes through multiple agent personas before applying them.
*   **Tool Calling & Interactive Guardrails**: Safe execution of files, shell commands, and search. Enforces real-time human capability authorization prompts under limited autonomy (v0.9.0).

### ⚡ Rust Control Plane (`neurex-cli`)
*   **Self-Provisioning**: Downloads and configures a hermetic Python environment via `uv` on first run — no pre-installed Python required.
*   **Process Management**: Keeps the API server and terminals alive independently of the browser session.
*   **Docker & WASM Sandboxing**: Runs agent-generated code in isolated containers.

### 🌐 Experimental Labs (Lower Priority)
*   **VRAM Pooling**: Distribute a model's layers across multiple machines via `llama-rpc-server` (functional but considered a niche power-user feature).
*   **Dynamic Re-quantization**: Automatically downgrades model precision (e.g., Q8 → Q4) under memory pressure to prevent stalls.
*   **Node Discovery & P2P Sync**: Registers peer machines and synchronizes active workspace directories dynamically over LAN via secure mTLS (v0.9.0).

### 📁 IDE Features
*   **Monaco Editor**: Full VS Code-grade editing with syntax highlighting and formatting.
*   **LSP Integration**: Connects to system-installed language servers for diagnostics and completion.
*   **Multi-Root Workspaces**: Manage multiple project roots in a single session.
*   **Persistent Terminals**: PTY sessions that reconnect after browser refresh.
*   **RAG & Swarm Collective Memory**: Cross-session cognitive persistence (Hive Mind) storing codebase architectural patterns, indexable via ChromaDB and local embedding models.

---

## 🏛️ Architecture

```mermaid
flowchart TD
    subgraph "Control Plane (neurex-cli)"
        CLI[Rust Daemon]
        PROV[uv Provisioner]
    end

    subgraph "API Layer (neurex-api)"
        ORCH[Orchestrator]
        TG[(Task Graph / SQLite)]
        PTY[PTY Manager]
        RAG[ChromaDB / Embeddings]
    end

    subgraph "Inference Layer"
        OLLAMA[Ollama / llama.cpp]
        RPC[llama-rpc-server Nodes]
    end

    User((Developer)) ==> UI[React Frontend]
    UI ==> WS[WebSocket / REST]
    CLI --> PROV
    CLI --> API
    WS --> ORCH
    ORCH --> TG
    ORCH --> PTY
    ORCH --> RAG
    ORCH --> OLLAMA
    OLLAMA --> RPC
```

---

## 🛠️ Tech Stack

| Layer | Technologies |
| :--- | :--- |
| **Frontend** | React 18, Vite, Zustand, Monaco Editor, Framer Motion |
| **Backend** | FastAPI, Python 3.11+, Asyncio, Pydantic v2 |
| **Control Plane** | Rust (Tokio, Axum), `uv` for Python env management |
| **Persistence** | SQLite (task graphs), ChromaDB (vector memory) |
| **Inference** | Ollama, llama.cpp, llama-rpc-server |

---

## 🏁 Getting Started

### 1. One-Click Bootstrap (Recommended)
Download the latest `neurex-cli` binary for your platform and run:
```bash
./neurex start
```
The CLI will provision a Python environment and install all dependencies automatically.

### 2. Manual Development Install
```bash
git clone https://github.com/RaveAgainstTheMachine/neurex.git
cd neurex/neurex-cli
cargo run -- start
```

See [INSTALL.md](./INSTALL.md) for full setup instructions.

---

## ⚖️ Licensing

Neurex is licensed under the **Business Source License 1.1** (BSL).

- **Non-Commercial Use**: Free for personal and educational use.
- **Commercial Use**: Free for entities with annual gross revenue below **$5,000,000 USD**.
- **Change Date**: On **January 1, 2030**, the license converts to the **Apache License, Version 2.0**.

See [LICENSE](./LICENSE) for full details.

---

<div align="center">
  <sub>Built by the Neurex Collective. v0.11.0.</sub>
</div>
