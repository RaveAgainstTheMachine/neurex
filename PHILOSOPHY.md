# Neurex: Philosophy & Positioning

## Why Neurex Exists

Most "AI IDEs" today are VS Code forks with a chat panel attached to a centralized API. That model has real tradeoffs: your code goes to a third party, you pay a monthly subscription for compute you don't own, and when you close the app your agent's context evaporates.

Neurex is built on a different premise: **your hardware, your models, your data**.

## Key Design Decisions

### 1. Local-First Inference
Neurex integrates with Ollama and llama.cpp, running open-weight models (Llama 3, Qwen, Mistral) entirely on your own hardware. No code leaves your network unless you explicitly configure an external provider.

### 2. Persistent State (PTY Decoupling)
The Rust control plane (`neurex-cli`) keeps the Python API and PTY terminals alive as independent processes. Closing your browser tab or refreshing the page does not destroy your active terminal sessions or agent context. When you reconnect, the buffer is replayed and the agent resumes where it left off.

### 3. Distributed Inference Across a LAN
If your codebase needs a 70B model that doesn't fit in one GPU's VRAM, Neurex can distribute the model's layers across multiple machines on your local network via `llama-rpc-server`. This is real, implemented functionality — not a roadmap item.

### 4. Agents as Collaborators
Rather than a black-box that writes to your files in the background, Neurex agents have visible presence in the IDE (cursors, file lock indicators) and operate through the same tool layer you do. The `CollaborationManager` prevents write collisions between concurrent agents and human developers.

## How Neurex Compares

| Dimension | Cursor / Windsurf | Replit Agent | Neurex |
| :--- | :--- | :--- | :--- |
| **Inference** | Centralized API (OpenAI/Anthropic) | Centralized (Replit-managed) | Local (Ollama / llama.cpp) |
| **Data Sovereignty** | Code sent to third-party API | Code hosted in cloud | Code stays local |
| **Terminal State** | Lost on restart | Ephemeral cloud container | Persists across browser disconnects |
| **Compute** | Subscription-based | Subscription-based | Your own GPU(s), optionally pooled across LAN |
| **Agent Visibility** | Background process | Black box | Visible cursors, file locks, reasoning traces |

## 🎯 The Killer Wedge: Autonomous Maintenance

While other AI IDEs focus on the *creative* act of writing new code, Neurex owns the *chore* of maintaining it.

We aim to be the industry standard for **Autonomous Repo Maintenance**:
- **Security Hardening**: Agents that autonomously patch command injections and path traversals.
- **Dependency Migration**: Handing an agent a `package.json` and saying "upgrade everything and fix the breaks."
- **Codebase Grounding**: Ensuring that documentation, rules, and code never drift apart.

## When to Use Neurex

**Good fit if:**
- You want to run AI agents against your codebase without sending code to a cloud API
- You have local GPU hardware (even a single consumer GPU works)
- You want persistent terminal sessions and task state across reconnects
- You want to pool inference across multiple local machines

**Not the right tool if:**
- You want a polished, zero-setup experience — Neurex requires some infrastructure setup
- You need tight VS Code plugin ecosystem compatibility
- You want the highest-capability models (GPT-4o, Claude Opus) — those require external API keys

---
*Updated for v0.15.4.*
