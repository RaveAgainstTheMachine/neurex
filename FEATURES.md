# Neurex Features

## 🎨 Design & UI
- **Glassmorphic Design System**: HSL-based translucency and blur effects throughout the interface.
- **Custom Typography**: 'Outfit' and 'Roboto Mono' fonts for readability.
- **Micro-animations**: State-aware transitions for AI activity indicators.

## 🧠 Code Intelligence
- **LSP Integration**: Connects to system-installed language servers (e.g., `pyright`, `rust-analyzer`, `clangd`) for diagnostics, completions, and formatting.
- **Inline Diagnostics**: Groups errors and warnings and renders them inline after the relevant code line.
- **Git Blame**: Real-time commit blame rendered as ghost-text decorations.
- **RAG / Codebase Search**: Semantic search over your project using local embedding models and ChromaDB.

## 🛠️ Editor & Productivity
- **Monaco Editor**: Full VS Code-grade editing experience.
- **Global Command Palette**: Searchable command center (Cmd+Shift+P).
- **Multi-Tab Search**: Grouped file results with search-and-replace.
- **Source Control**: Native Git staging and commit interface.
- **Interactive Status Bar**: Control over indentation, encoding, and language mode.
- **Multi-Root Workspaces**: Manage multiple project roots simultaneously with root-scoped file operations and terminals.

## 🤖 Agentic Capabilities
- **Task Orchestration**: Persistent, SQLite-backed task graphs for multi-step engineering goals.
- **Role-Based Model Routing**: Assign different models (e.g., Llama for coding, Qwen for planning) to different cognitive roles independently.
- **Tool Calling**: Agents can read/write files, run shell commands, and perform semantic search.
- **Docker Sandbox**: Agent-generated code runs in an isolated Docker container with restricted networking and filesystem access.

## 🌐 Distributed Inference (LAN)
- **VRAM Pooling**: Distribute model layers across multiple LAN machines via `llama-rpc-server`.
- **Node Monitoring**: Real-time tracking of peer node GPU load and VRAM utilization.
- **Dynamic Re-quantization**: Automatically downgrades model precision under memory pressure.

## 🐚 Terminal
- **Persistent PTY Sessions**: Terminals stay alive across browser refreshes and reconnections.
- **Multiplexed Tabs**: Multiple independent terminal sessions with per-session routing.

## 🧩 Skills / Extensibility
- **Skill Discovery**: Interface for discovering and installing agentic toolsets.
- **Git-based Install**: Install skills directly from Git repositories.

---

## ⚡ Active Development in v0.6.0 (The Interactive Agentic Pivot)
- **Visual Agent Task Graph Editor**: A node-based designer canvas where users can visually rewire task dependencies, insert manual/agent steps, and set active execution breakpoints.
- **Multi-Cursor AI Pair Programming**: Real-time collaborative typing in Monaco with visual AI cursors (`[Neurex Coder]`), selection highlights, and 60Hz telemetry sync.
- **Bidirectional LSP Context Router**: Exposing language server operations (`find references`, `go to definition`, `diagnostics`) directly to agents to query semantic codebase relations.
- **Visual MCP Tool Sandbox & Manager**: A dashboard listing connected Model Context Protocol servers with a granular permission matrix (Always Allow, Always Ask, Deny) and manual tool playgrounds.

