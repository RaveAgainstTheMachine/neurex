<div align="center">
  <img src="./assets/neurex_splash.png" width="100%" alt="Neurex Sentient IDE">
  
  <br />

  <h1>⬡ NEUREX</h1>
  <h3>The Universal Sentient IDE Substrate & Neural Mesh Hub</h3>

  <p>
    <a href="https://opensource.org/licenses/MIT"><img src="https://img.shields.io/badge/License-MIT-purple.svg?style=for-the-badge" alt="License"></a>
    <a href="#"><img src="https://img.shields.io/badge/Version-v0.4.0--NOC-blueviolet.svg?style=for-the-badge" alt="Version"></a>
    <a href="#"><img src="https://img.shields.io/badge/Status-Phase%2055%20Stable-success.svg?style=for-the-badge" alt="Status"></a>
    <a href="#"><img src="https://img.shields.io/badge/Platform-Linux%20%7C%20macOS%20%7C%20Win-white.svg?style=for-the-badge" alt="Platform"></a>
  </p>

  <p align="center">
    <i>"An IDE that doesn't just execute; it evolves with you."</i>
    <br />
    <b>Built for Human-Agent Parity.</b>
  </p>

  <p align="center">
    <a href="./wiki/Home.md"><b>Documentation</b></a> •
    <a href="./wiki/Changelog.md"><b>Changelog</b></a> •
    <a href="http://10.10.10.147:3000/frosty/neurex/issues"><b>Report Bug</b></a> •
    <a href="./ROADMAP.md"><b>Roadmap</b></a>
  </p>
</div>

---

## 👁️ The Vision
**Neurex** is a high-performance, autonomous development substrate designed to bridge the gap between human intent and agentic execution. Unlike traditional IDEs, Neurex operates as a **Sentient Mesh**—a decentralized network of AI agents that manage their own infrastructure, repair their own regressions, and maintain architectural integrity through a global consensus protocol.

---

## 🚀 Key Pillars

### 🧠 Sentient Autonomy
*   **Infrastructure NOC**: Real-time telemetry for storage health, multi-disk environments, and "Hot/Cold" model states.
*   **Neural Self-Repair**: Autonomous agents that detect, analyze, and fix their own regressions in real-time.
*   **Neural Linter**: Architectural validation of every code mutation against project-specific design laws.
*   **Swarm Consensus**: Democratic governance for critical assets, requiring multi-agent approval for core mutations.

### ⚡ Kinetic Performance
*   **Hermetic Substrate**: Zero-dependency distribution via a native Rust daemon and autonomous `uv` provisioning.
*   **Glassmorphic UI**: A high-fidelity, GPU-accelerated interface designed for deep architectural focus.
*   **Predictive Prefetching**: Eliminates cold-start latency by warming model weights based on agent trajectory.

### 🌐 Universal Connectivity
*   **Federated RAG 2.0**: Semantic and relational retrieval across the entire Mesh.
*   **Neural Virtualization**: Mesh-wide VRAM pooling and autonomous re-quantization to fit distributed hardware.
*   **Native Gitea Sync**: Professional issue tracking and substrate synchronization directly with the origin server.

---

## 🏛️ Architecture

<div align="center">
  <a href="./assets/neurex_arch.png" target="_blank">
    <img src="./assets/neurex_arch.png" width="100%" alt="Neurex Isometric Architecture (Click to Zoom)">
  </a>
  <p><i>Click the diagram above to explore the high-fidelity isometric substrate.</i></p>
</div>

<details>
<summary><b>View Stylized Logic Flowchart</b></summary>

```mermaid
flowchart TD
    subgraph "Neural Mesh Hub"
        POOL[Attention Coordinator] --- SHARD[Context Sharder]
        SHARD --- PEERS[Federated Peer Nodes]
        PREFETCH[Predictive Prefetcher] -.-> POOL
    end

    subgraph "Sentient Core"
        ORCH[Orchestrator / Supervisor] --- TG[Task Graph Ledger]
        ORCH --- LINT[Neural Linter]
        LINT --- REPAIR[Self-Repair Loop]
        ORCH --- CONS[Swarm Consensus]
    end

    User((Developer)) == Request ==> UI[Glassmorphic Frontend]
    UI == Bridge ==> WS[WebSocket / API Hub]
    WS == Control ==> ORCH
    
    ORCH == Federated Search ==> RAG[Distributed RAG / Hive Mind]
    ORCH == Telemetry ==> NOC[Infrastructure NOC]
    
    ORCH <== Neural Link ==> POOL

    %% Styling
    classDef core fill:#9c6fff33,stroke:#9c6fff,stroke-width:2px,color:#fff
    classDef mesh fill:#00d2ff33,stroke:#00d2ff,stroke-width:2px,color:#fff
    classDef io fill:#050507,stroke:#333,stroke-width:1px,color:#888
    
    class ORCH,TG,LINT,REPAIR,CONS core
    class POOL,SHARD,PEERS,PREFETCH mesh
    class UI,WS,RAG,NOC io
```

</details>

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
git clone http://10.10.10.147:3000/frosty/neurex.git
cd neurex/neurex-cli
cargo run -- start
```

---

## 📜 Source of Law
Neurex development is governed by the **Anti-Gravity Protocol** (see `.antigravityrules`). All mutations must be protocol-aligned, documented, and verified by the Neural Linter.

---

<div align="center">
  <sub>Built with 💜 by the Neurex Collective. Phase 55 Stable.</sub>
</div>
