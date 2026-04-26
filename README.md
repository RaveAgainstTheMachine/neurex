# Neurex — Federated Agentic IDE

Neurex is an open-source development platform that aggregates local compute resources into a federated mesh for large-scale model inference and multi-agent software engineering.

## Architecture Overview

Neurex utilizes a Master-Worker architecture to pool distributed VRAM and execute agentic workflows:

- **Distributed Inference**: Uses `llama-rpc-server` to pool GPU resources across the local network.
- **Agent Orchestration**: State-persistent task graphs managed by specialized personas (Planner, Coder, Reviewer).
- **Collective Memory**: ChromaDB-backed vector store with Tree-Sitter chunking for codebase awareness.
- **Secure Sandbox**: Docker-isolated terminal and test execution with no network access.

## Quick Start

### 1. Requirements
- Linux (Ubuntu/Debian/CachyOS recommended)
- Docker + NVIDIA Container Toolkit (for sandbox and local GPU support)
- Python 3.14+
- Node.js 20+

### 2. Installation
```bash
git clone https://github.com/USERNAME/neurex.git
cd neurex
bash install.sh
```
Follow the prompts to configure your node as a **Master** or **RPC Worker**.

### 3. Launch
**Master Node:**
```bash
docker compose up -d
```
Access the interface at `http://localhost:3000`.

**Worker Node:**
```bash
docker compose -f docker-compose.node.yml up -d
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

---
Built by Steven Frost with the assistance of Antigravity.
