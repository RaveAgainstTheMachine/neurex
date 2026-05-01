# ⬡ Neurex: The Agentic IDE & Unified Mesh Hub

[![License: MIT](https://img.shields.io/badge/License-MIT-purple.svg)](https://opensource.org/licenses/MIT)
[![Version: 0.8.4-alpha](https://img.shields.io/badge/Version-0.8.4--alpha-blueviolet.svg)](#)
[![Depth: High](https://img.shields.io/badge/Design-Glassmorphism-9c6fff.svg)](#)

**Neurex** is a high-performance, sentient-inspired IDE designed for the age of agentic software development. It transforms the developer workspace into a collaborative substrate where humans and AI agents work with **Human-Agent Parity**.

---

## 🌓 Core Pillars

*   **State Persistence**: Terminal sessions, file buffers, and agent thinking states survive disconnections and refreshes.
*   **Infrastructure Hub**: A command center for managing vLLM, Ollama, and llama.cpp engines with real-time VRAM/RAM metrics.
*   **Unified Mesh**: Seamlessly route inference tasks across local GPUs and remote peer nodes.
*   **Aesthetic Integrity**: A deep-obsidian, glassmorphic UI designed for focus and kinetic flow.

---

## 🚀 Quick Start

### 1. Prerequisites
- **Python 3.10+** (Backend)
- **Node.js 18+** (Frontend)
- **Ollama** (Recommended for local inference)
- **NVIDIA GPU** (Optional, but recommended for Blackwell/Ada acceleration)

### 2. Installation
```bash
# Clone the repository
git clone https://github.com/antigravity/neurex.git
cd neurex

# Run the automated installer
./install.sh
```

### 3. Launch
```bash
./launch_neurex.sh
```
*The IDE will be available at `http://localhost:3000`.*

---

## 🏛️ Architecture

Neurex is built on a distributed, asynchronous backbone:

- **Frontend**: Vite + React + Zustand + Monaco Editor.
- **Backend**: FastAPI + Python 3.11 with an asynchronous Orchestrator.
- **Inference**: Native support for Ollama, llama.cpp (GGUF), and vLLM.
- **Persistence**: SQLite-backed task graphs and chat history.

For a deep dive into the system logic, see [PHILOSOPHY.md](./PHILOSOPHY.md).

---

## 🛠️ Infrastructure Hub

Neurex includes a built-in **Infrastructure Hub** (InfraPanel) that allows you to:
- **Monitor**: Real-time system resource usage (VRAM, RAM, CPU).
- **Deploy**: Download and quantify models directly from Hugging Face with 4-bit/8-bit auto-selection.
- **Skills**: Toggle agent toolsets (MCP) like `filesystem`, `web_search`, and `terminal`.
- **Mesh**: Connect to peer nodes to pool VRAM for large model inference.

---

## 🎨 Design System

Our UI/UX standards are documented in [DESIGN_SYSTEM.md](./DESIGN_SYSTEM.md). We prioritize:
- **Depth**: Translucency and backdrop-blur.
- **Motion**: Cubic-bezier kinetic transitions.
- **Clarity**: Zero-ambiguity status indicators.

---

## 🗺️ Roadmap & Wiki

- **Development Status**: [neurex_development_plan.md](./neurex_development_plan.md)
- **Hardware Tier List**: [HARDWARE_BENCHMARKS.md](./HARDWARE_BENCHMARKS.md)
- **Contribution Guide**: [CONTRIBUTING.md](./CONTRIBUTING.md)
- **Philosophy**: [PHILOSOPHY.md](./PHILOSOPHY.md)

---

## ⬡ Credits & Acknowledgements
Developed by **Steven Frost** with architectural assistance and agentic core development by **Antigravity**.
