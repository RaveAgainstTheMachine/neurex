# Neurex Core Philosophy

Neurex is not just a tool; it is a collaborative substrate designed for the age of agentic software development. Its architecture is guided by five foundational pillars.

## 1. The Persistence Principle
*“State is sacred.”*
In Neurex, a browser refresh is a visual event, not a destructive one. Terminal sessions, active files, scroll positions, and even AI "thinking" states must persist across disconnections. We leverage persistent PTY sessions on the backend and deep `localStorage` integration on the frontend to ensure the workspace is exactly as you left it.

## 2. The Ghost in the Machine (Aesthetic Integrity)
*“Precision over polish.”*
The UI must feel like a high-performance sentient operating system. This is achieved through:
- **Kinetic Motion**: Transitions must be smooth and continuous (no jerky jumps).
- **Depth & Translucency**: Glassmorphism is used to show the "plasma" underlays, simulating a living digital organism.
- **Visual Accuracy**: Progress bars and status indicators must represent real-time data flow with absolute precision.

## 3. Human-Agent Parity
*“Collaboration, not just automation.”*
Agents in Neurex are first-class citizens. They possess their own cursors, their own file locks, and their own terminal presence. The system is designed so that humans and agents can pair-program in the same file simultaneously without race conditions, mediated by the `CollaborationManager`.

## 4. Zero-Ambiguity Interface
*“Clarity is safety.”*
In a workspace where an agent can execute shell commands, there is no room for ambiguity. 
- **Explicit Indicators**: Toggles must literally say "ON" or "OFF".
- **Transparent Logic**: Every agent action requires a clear approval path unless explicitly granted full autonomy.
- **Technical Honesty**: We avoid marketing superlatives in the UI, focusing instead on functional impact and status transparency.

## 5. Defensive Autonomy
*“Safe by default, powerful by command.”*
The system defaults to a "Restricted" autonomy model. Agents are sandboxed and monitored by the core `CoreLogic` engine. As trust is established, users can scale autonomy levels, but the "Approval required" handshake remains the primary safeguard against destructive execution.

## 6. Resilient Recovery & Disaster Prevention
*“Fail small, recover fast.”*
In an agent-driven environment, disaster prevention is an architectural requirement, not an afterthought.
- **One-Way Trash Policy**: Neurex enforces a non-destructive delete policy. Files "deleted" by agents are moved to a hardened `.neurex/trash` directory. Agents have zero permissions to read from or write to this directory, preventing accidental or malicious permanent data loss.
- **Sandbox Isolation**: All terminal executions occur within an ephemeral Docker sandbox with no network access by default. This ensures that even a runaway script cannot impact the host system or external infrastructure.
- **Fail-Safe State Transition**: If the master node detects a logic stall or a WebSocket disconnection during a multi-step task, the agent immediately halts and reverts to an "AWAITING_APPROVAL" state. It will not attempt to proceed until a human operator re-establishes context.
- **Atomic Persistence**: Every task result and terminal output is journaled to a persistent SQLite graph. This allows for full "re-entry" and disaster recovery after a power loss or system crash, ensuring no data or context is lost in the ether.

## 7. Unified Mesh Intelligence
*“Compute is a utility.”*
Neurex treats inference and compute as a unified, fungible resource. Whether it's a local GPU, a peer node in the mesh, or a specialized cloud provider, the system abstracts the underlying hardware into a single "Infrastructure Hub." This allows for seamless task routing and distributed intelligence without manual configuration.
