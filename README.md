# Neurex: Agentic AI IDE ⬡

Neurex is a high-performance, agentic development environment designed for local-first AI coding. It features a Windsurf-style UI built with Vite, Monaco Editor, and a multi-agent backend that can plan, code, and test autonomously.

## 🏗️ Architecture

- **Frontend**: Vite + React + TypeScript + Monaco Editor + Xterm.js
- **Backend**: FastAPI + SQLModel (SQLite) + Orchestrator
- **Intelligence**: Local LLMs via Ollama (Qwen2.5-Coder, DeepSeek-R1)
- **Memory**: ChromaDB for RAG context (Local Persistent Client)
- **Sandbox**: Docker-isolated execution environment for tools

## 🚀 Quick Start

### 1. Prerequisites
- **Python 3.12+**
- **Node.js 20+**
- **Ollama** (running locally)
- **Docker** (optional, for tool sandboxing)

### 2. Setup
Run the setup script to initialize environment variables and pull models:
```bash
bash setup_neurex.sh
```

### 3. Run Development Servers

#### Backend
```bash
cd neurex-api
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python main.py
```

#### Frontend
```bash
cd neurex-web
npm install
npm run dev
```

Visit `http://localhost:3000` to start coding.

## 🛠️ Features

- **Agentic Workflow**: Agents generate plans, ask for approval, and execute complex refactors.
- **Human-in-the-Loop**: Approval gateway for sensitive operations like shell commands or major file writes.
- **RAG-Powered Context**: Automatic codebase indexing for context-aware coding assistance.
- **Monaco Integration**: Familiar VS Code-like editing experience with syntax highlighting and multi-tab support.

## 📜 Project Rules
Check [.neurexrules](.neurexrules) for specific coding standards and agent behavioral guidelines.

---
*Built with Neurex, for Neurex.*
