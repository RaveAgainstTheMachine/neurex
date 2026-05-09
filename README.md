<div align="center">
  <img src="./assets/neurex_splash.png" width="100%" alt="Neurex Agentic IDE">
  
  <br />

  <h1>⬡ NEUREX</h1>
  <h3>The first autonomous workspace for the neural era.</h3>

  <p align="center">
    <b>Stop chatting with your IDE. Start engineering with your mesh.</b>
  </p>

  <p>
    <a href="./LICENSE"><img src="https://img.shields.io/badge/License-BSL%201.1-purple.svg?style=for-the-badge" alt="License"></a>
    <a href="#"><img src="https://img.shields.io/badge/Version-v0.5.2--DYNAMIC-blueviolet.svg?style=for-the-badge" alt="Version"></a>
    <a href="#"><img src="https://img.shields.io/badge/Status-Phase%2061%20Stable-success.svg?style=for-the-badge" alt="Status"></a>
  </p>

  <p align="center">
    <i>"An IDE that doesn't just execute; it evolves with you."</i>
    <br />
    <b>Built for Human-Agent Parity.</b>
  </p>

  <p align="center">
    <a href="./wiki/Home.md"><b>Documentation</b></a> •
    <a href="./wiki/Changelog.md"><b>Changelog</b></a> •
    <a href="./CREDITS.md"><b>Credits</b></a> •
    <a href="./ROADMAP.md"><b>Roadmap</b></a>
  </p>
</div>

---

## 👁️ The Essence
**Neurex** is an autonomous engineering workspace designed for human-agent parity. 

It transforms your infrastructure into a **Neural Mesh**—a decentralized network where agents are your peers, hardware is pooled via distributed VRAM, and the system autonomously heals regressions. Stop chatting with your IDE; start engineering with your mesh.

---

## 🚀 The Core Experience

### 🧠 Collaborative Intelligence
*   **Agentic Peers**: Work alongside agents with their own visual cursors and persistent state.
*   **Role Routing**: Dynamically assign models (GPT-4, Claude, Llama 3) to specific tasks like planning or testing.
*   **Swarm Consensus**: High-risk changes require multi-agent validation before they hit your disk.
*   **Persistent Context**: Task graphs that survive crashes, restarts, and network drops.

### ⚡ High-Performance Substrate
*   **Rust Control Plane**: A native daemon that keeps your terminals and background tasks alive forever.
*   **Zero-Config Setup**: One-click bootstrap that manages its own hermetic Python and Rust environments.
*   **Safe Execution**: Built-in Docker and WASM sandboxing for non-destructive agent operations.
*   **Real-time Telemetry**: Sub-millisecond observability into exactly what your agents are thinking.

### 🌐 Resource Sovereignty
*   **VRAM Pooling**: Combine the GPU power of every machine on your network into a single "unified brain."
*   **Adaptive Precision**: Automatically shifts model quality to maintain speed when your hardware is under load.
*   **Hive Mind**: Shared relational memory across your entire engineering mesh.
*   **Zero Latency**: Predictive model pre-loading so your agents are always ready to code.

---

## 🏛️ Architecture

```mermaid
flowchart TD
    %% Zones
    subgraph "Orchestration Core"
        ORCH[Orchestrator / Supervisor]
        TG[(Task Graph Ledger)]
        LINT[Neural Linter]
        CONS[Swarm Consensus]
        REPAIR[Self-Repair Loop]
    end

    subgraph "Neural Mesh Hub"
        POOL[Attention Coordinator]
        SHARD[Context Sharder]
        PEERS[Federated Peer Nodes]
        PREFETCH[Predictive Prefetcher]
    end

    subgraph "Infrastructure NOC"
        TELEMETRY[Real-time Metrics]
        HEALTH[Storage Health]
        MODELS[Model Lifecycle]
    end

    %% IO Layer
    User((Developer)) == Request ==> UI[Glassmorphic Frontend]
    UI == Bridge ==> WS[WebSocket / API Hub]
    WS == Control ==> ORCH

    %% Internal Connections
    ORCH --- TG
    ORCH --- LINT
    ORCH --- CONS
    LINT --- REPAIR
    
    ORCH <== Neural Link ==> POOL
    POOL --- SHARD
    SHARD --- PEERS
    PREFETCH -.-> POOL

    ORCH == Monitoring ==> TELEMETRY
    TELEMETRY --- HEALTH
    TELEMETRY --- MODELS

    ORCH == Intelligence ==> RAG[Distributed RAG / Hive Mind]

    %% Professional Styling
    classDef core fill:#9c6fff15,stroke:#9c6fff,stroke-width:2px,color:#fff
    classDef mesh fill:#00d2ff15,stroke:#00d2ff,stroke-width:2px,color:#fff
    classDef infra fill:#22c55e15,stroke:#22c55e,stroke-width:2px,color:#fff
    classDef io fill:#0f172a,stroke:#334155,stroke-width:1px,color:#94a3b8

    class ORCH,TG,LINT,CONS,REPAIR core
    class POOL,SHARD,PEERS,PREFETCH mesh
    class TELEMETRY,HEALTH,MODELS infra
    class UI,WS,RAG io
```

---

## 🛠️ Tech Stack

| Layer | Technologies |
| :--- | :--- |
| **Frontend** | React 18, Vite, Zustand, Monaco Editor, Framer Motion |
| **Backend** | FastAPI, Python 3.14+, Asyncio, Pydantic v2 |
| **Core Daemon** | Rust 1.80, Tokio, Axum, Sysinfo |
| **Persistence** | SQLite (Tasks), ChromaDB (Vector Memory), SkepticalMemory |
| **Inference** | llama-cpp-python, vLLM, Ollama, NeuralHarness v2.0 |

---

## 🏁 Getting Started

### 1. One-Click Bootstrap (Recommended)
Download the latest `neurex-cli` for your platform and run:
```bash
./neurex start
```
*Neurex will autonomously provision its own hermetic Python environment and dependencies via the `uv` engine.*

### 2. Manual Development Install
```bash
git clone https://github.com/RaveAgainstTheMachine/neurex.git
cd neurex/neurex-cli
cargo run -- start
```

---

## 📜 Project Governance
Neurex development is governed by the **Neurex Core Protocol** (see `.projectrules`). All mutations must be protocol-aligned, documented, and verified by the Neural Linter.

---

## ⚖️ Licensing

Neurex is licensed under the **Business Source License 1.1** (BSL). 

- **Non-Commercial Use**: Completely free for personal and educational use.
- **Commercial Use**: Free for entities with annual gross revenue below **$5,000,000 USD**.
- **Change Date**: On **January 1, 2030**, the license will automatically convert to the **Apache License, Version 2.0**.

For full details, please refer to the [LICENSE](./LICENSE) file.

---

<div align="center">
  <sub>Built with 💜 by the Neurex Collective. Phase 61 Stable.</sub>
</div>
