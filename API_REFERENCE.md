# Neurex API Reference

> **Base URL**: `https://localhost:3000` (Control Plane Gateway)  
> **Internal API**: `http://localhost:8000`  
> **Auth**: Bearer JWT (obtain via `POST /api/auth/token`)  
> **WebSocket**: `wss://localhost:3000/ws/{conversation_id}` (Internal: `ws://localhost:8000/ws/...`)  
> **Version**: 0.6.0 (THE INTERACTIVE AGENTIC PIVOT)

---

## Navigation

- [Authentication](#authentication)
- [Projects & Collaboration](#projects--collaboration)
- [Chat & Conversations](#chat--conversations)
- [Task Graph](#task-graph)
- [Files](#files)
- [Infrastructure & Mesh](#infrastructure--mesh)
- [Hive Mind (Memory)](#hive-mind-memory)
- [Language Intelligence & LSP](#language-intelligence--lsp)
- [Git & Version Control](#git--version-control)
- [Skills & Extensions](#skills--extensions)
- [Model Context Protocol & MCP](#model-context-protocol-mcp--sandbox)
- [Settings](#settings)
- [Notifications](#notifications)
- [Self-Update](#self-update)
- [WebSocket Protocol](#websocket-protocol)
- [Error Reference](#error-reference)

---

*   **Swarm Telemetry**: Real-time observability via the **Flight Recorder**, capturing every architectural pivot and tool reasoning trace.
*   **Operational Transparency**: Visual audit trail of autonomous decisions directly within the IDE.

## 1. Authentication

All endpoints (except `/health`, `/api/auth/register`, `/api/auth/token`) require a Bearer JWT. 

> [!IMPORTANT]
> **JWT_SECRET**: The API will refuse to start if the `JWT_SECRET` environment variable is not set.

**Roles**: `admin` > `developer` > `viewer`

### 1.1 Proxy Transparency (Phase 60)

When connecting via the **Neurex CLI Substrate**, all requests are proxied. To ensure session integrity and correct origin validation, the proxy injects the following headers:

| Header | Description |
|:---|:---|
| `X-Forwarded-For` | The real IP address of the client device. |
| `X-Forwarded-Proto` | The external protocol (`https`). |
| `X-Forwarded-Host` | The external hostname (e.g., `neurex.local`). |

The backend automatically utilizes these headers to validate CORS origins and protocol-sensitive auth callbacks.

### `POST /api/auth/register`
Register a new user. The **first** user registered is automatically granted `admin` role.

**Body** (`application/x-www-form-urlencoded`):
| Field | Type | Description |
|:---|:---|:---|
| `invite_code` | string | **Mandatory**. A valid, unused invitation token. |
| `username` | string | Unique username |
| `password` | string | Plain-text password (hashed server-side with pbkdf2_sha256) |

**Response `200`**:
```json
{ "message": "Account created with role: developer", "role": "developer" }
```

---

### `POST /api/auth/invite/create`
Generate a new invitation code.

**Auth**: `admin`

**Body**:
```json
{
  "role": "developer",
  "expires_in_hours": 24
}
```

**Response `200`**:
```json
{
  "invite_code": "code-123",
  "role": "developer",
  "expires_at": "2026-04-29T..."
}
```

---

### `POST /api/auth/token`
Authenticate and receive a JWT. Token lifetime: **24 hours**.

**Body** (`application/x-www-form-urlencoded`):
| Field | Type |
|:---|:---|
| `username` | string |
| `password` | string |

**Response `200`**:
```json
{
  "access_token": "eyJhbGci...",
  "token_type": "bearer",
  "role": "developer"
}
```

---

### `GET /api/auth/me`
Returns the current authenticated user's profile.

**Auth**: Any role

**Response `200`**:
```json
{ "username": "frosty", "role": "admin", "id": "uuid-..." }
```

---

## Projects & Collaboration

Manage multi-user workspaces, roles, and project-specific tasks.

### `GET /api/projects/`
List all projects the current user is a member of.

**Response `200`**: Array of `Project` objects.

---

### `POST /api/projects/`
Create a new project. The creator is automatically assigned the `owner` role.

**Body**:
```json
{ "name": "Project Alpha", "description": "Experimental mesh node" }
```

---

### `GET /api/projects/{project_id}/members`
List all members and their roles for a project.

**Roles**: `owner`, `admin`, `member`, `viewer`, `agent`

---

### `POST /api/projects/{project_id}/members`
Invite or add a user to a project.

**Body**:
```json
{ "user_id": "uuid-...", "role": "member" }
```

---

## Chat & Conversations

The primary interaction path is the WebSocket. These REST endpoints hydrate history on page load and persist messages.

### `GET /api/chat/conversations`
Returns all conversation IDs sorted by most recent activity.

**Auth**: Any role

**Response `200`**:
```json
[
  { "conversation_id": "abc-123", "last_message": "2026-04-25T14:00:00" }
]
```

---

### `GET /api/chat/{conversation_id}`
Fetch message history for a conversation.

**Query params**:
| Param | Default | Description |
|:---|:---|:---|
| `limit` | `100` | Max messages to return (newest-last) |

**Response `200`**: Array of `ChatMessage` objects:
```json
[
  {
    "id": "uuid",
    "conversation_id": "abc-123",
    "role": "user",
    "content": "Refactor this module",
    "graph_id": "graph-uuid-or-null",
    "created_at": "2026-04-25T10:00:00"
  }
]
```

---

### `POST /api/chat/message`
Persist a chat message. Called internally by the WebSocket handler after each exchange.

**Body**:
```json
{
  "conversation_id": "abc-123",
  "role": "assistant",
  "content": "I've completed the refactor.",
  "graph_id": "optional-graph-uuid"
}
```

---

### `DELETE /api/chat/{conversation_id}`
Clear all messages for a conversation.

**Response `200`**:
```json
{ "deleted": true, "conversation_id": "abc-123" }
```

---

## Task Graph

The Task Graph is the execution ledger for agentic operations. All agent tasks are persisted in SQLite.

**Task Statuses**: `pending` → `thinking` → `awaiting_approval` → `writing` → `testing` → `done` / `failed` / `cancelled`

### `GET /api/tasks/`
List all tasks. Filter by graph with `?graph_id=`.

**Query params**:
| Param | Description |
|:---|:---|
| `graph_id` | Optional. Filter to a specific execution graph |

**Response `200`**: Array of `TaskNode` objects:
```json
[
  {
    "id": "task-uuid",
    "parent_id": null,
    "graph_id": "graph-uuid",
    "agent_type": "coder",
    "title": "Implement auth middleware",
    "description": "...",
    "status": "done",
    "approval_reason": null,
    "result": "OK: wrote 340 chars to middleware.py",
    "error": null,
    "iteration": 3,
    "max_iterations": 10
  }
]
```

---

### `GET /api/tasks/{graph_id}`
Fetch all nodes for a specific execution graph (tree structure via `parent_id`).

---

### `POST /api/tasks/{graph_id}/approve_all`
Approve all `awaiting_approval` and `pending` tasks in a graph, transitioning them to `pending` so the orchestrator resumes.

**Auth**: Any role (approval is an intentional HITL action)

---

### `POST /api/tasks/{graph_id}/cancel`
Cancel all non-completed tasks in a graph. Immediately halts orchestrator execution for this graph.

**Auth**: `developer` or higher

---

### `DELETE /api/tasks/`
Purge all task records. Useful for cleanup.

---

## Files

All paths are relative to `WORKSPACE_PATH`. Path traversal and access to `.neurex/trash` are blocked at the resolver level.

### `GET /api/files/`
List workspace directory contents.

**Query params**:
| Param | Default | Description |
|:---|:---|:---|
| `path` | `.` | Relative directory path |
| `root_path` | null | **Optional**. The project root for multi-folder workspaces. |

**Response `200`**:
```json
[
  { "name": "main.py", "type": "file", "size": 3200, "modified": "2026-04-25T10:00:00" }
]
```

---

### `POST /api/files/save`
Write or overwrite a file. Acquires a collaboration lock before writing.

**Body**:
```json
{ "path": "src/utils.py", "content": "def foo(): ...", "root_path": "optional-root" }
```

**Auth**: `developer` or higher  
**Note**: In `restricted` autonomy ceiling mode, writes from agents return `APPROVAL_REQUIRED`.

---

### `POST /api/files/upload`
Upload a binary file to the workspace.

**Body**: `multipart/form-data`  
| Field | Description |
|:---|:---|
| `file` | The file binary |
| `path` | Destination directory (default: `uploads`) |

---

### `GET /api/files/search`
Search for files matching a query (filename substring).

**Query params**: `?query=auth&root_path=/abs/path`

---

### `GET /api/files/stage`
Retrieve the list of files currently in the `.neurex/staging` directory, showing their paths and whether they are modified or deleted.

**Response `200`**:
```json
[
  { "path": "src/utils.py", "status": "modified" },
  { "path": "tests/old_test.py", "status": "deleted" }
]
```

---

### `POST /api/files/stage/commit`
Apply all staged changes from `.neurex/staging` to the actual workspace and clear the staging directory.

**Response `200`**:
```json
{ "status": "ok", "committed_count": 2 }
```

---

### `POST /api/files/stage/clear`
Clear all staged changes from `.neurex/staging` without applying them.

**Response `200`**:
```json
{ "status": "ok", "message": "Staging cleared successfully." }
```

---

## Infrastructure & Mesh

### `GET /api/infra/status`
Returns full infrastructure status: LLM engine states, system metrics (CPU, RAM, VRAM), hardware benchmarks, and project intelligence.

**Response `200`**:
```json
{
  "engines": [
    { "name": "ollama", "is_running": true, "version": "0.3.3" }
  ],
  "metrics": {
    "cpu_percent": 12.4,
    "ram_total_gb": 64.0,
    "ram_used_gb": 22.1,
    "vram_gb": 10.2,
    "benchmarks": { "tps": 45.2, "load_ms": 1200 },
    "intel": { "tech_stack": ["Python", "Docker"], "architecture": "..." }
  },
  "peers": [],
  "queue_depth": 0
}
```

---

### `POST /api/infra/engine/{name}/start`
Start a named LLM engine (e.g. `ollama`).

**Auth**: `admin`

---

### `POST /api/infra/engine/{name}/stop`
Stop a named LLM engine.

**Auth**: `admin`

---

### `GET /api/infra/recommend`
Recommend the optimal model for a given task type.

**Query params**: `?task=code_generation`

---

### `GET /api/infra/registry`
Returns the full model registry: all known models, their capabilities, and recommended use cases.

---

### `GET /api/infra/skills`
List infrastructure-level skills (differs from `/api/skills` — these are engine-level capabilities).

---

### `POST /api/infra/skills/{skill_id}/toggle`
Enable or disable an infrastructure skill.

**Auth**: `admin`  
**Query params**: `?enable=true`

---

### `POST /api/infra/benchmark/{model}`
Run a tokens-per-second benchmark on a specific model.

**Auth**: `developer` or higher

---

### `GET /api/infra/mesh/peers`
List all registered swarm peers and their last-known status.

**Response `200`**:
```json
[
  {
    "url": "http://192.168.1.20:8080",
    "name": "workstation-2",
    "status": "online",
    "vram_gb": 16.0,
    "latency_ms": 8,
    "queue_depth": 0
  }
]
```

---

### `POST /api/infra/mesh/peers`
Register a new peer node in the mesh.

**Auth**: `admin`  
**Body**:
```json
{ "url": "http://192.168.1.20:8080", "token": "node-api-token", "name": "workstation-2" }
```

---

### `DELETE /api/infra/mesh/peers`
Remove a peer from the mesh roster.

**Auth**: `admin`  
**Query params**: `?url=http://192.168.1.20:8080`

---

### `POST /api/infra/ollama_proxy/{path}`
Proxy an Ollama API request to the best available mesh node (selected by MeshRouter weighted-load algorithm).

**Auth**: `developer` or higher

---

### `GET /api/infra/mesh/topology`
Returns a detailed breakdown of swarm health, VRAM utilization, and queue depth for all connected nodes.

---

### `POST /api/infra/mesh/suitability`
Verify which mesh node is optimal for a specific model requirement.

---

## Hive Mind (Memory)

The Hive Mind is a ChromaDB-backed semantic vector store. All code written by agents and humans is automatically indexed by the `MemoryWorker`.

### `GET /api/memory/search`
Perform a semantic similarity search across the collective memory.

**Query params**:
| Param | Default | Description |
|:---|:---|:---|
| `q` | required | Natural language search query |
| `n_results` | `5` | Number of results to return |

**Response `200`**:
```json
{
  "results": [
    {
      "id": "chunk-uuid",
      "content": "async def verify_token(token: str) -> User:",
      "metadata": { "file": "api/routes/auth.py", "timestamp": "2026-04-25T10:00:00" },
      "distance": 0.12
    }
  ]
}
```

---

### `GET /api/memory/stats`
Returns metadata about the current Hive Mind state.

**Response `200`**:
```json
{
  "total_nodes": 1,
  "memory_count": 2847,
  "collection_name": "neurex_collective"
}
```

---

### `POST /api/memory/clear`
Wipe the entire collective memory store.

**Auth**: `admin` ⚠️ Destructive — irreversible.

---

---

## Language Intelligence & LSP

Neurex provides a native LSP Hub that bridges standard Language Server Protocol traffic from system-installed servers to the web interface.

### `GET /api/languages/supported`
Returns a list of languages that have a detected LSP on the host system.

**Response `200`**:
```json
{ "languages": ["python", "typescript", "rust", "go"] }
```

### `WS /api/websocket/ws/lsp/{lang}`
WebSocket bridge for raw LSP JSON-RPC traffic. Acts as a transparent proxy to the backend LSP process.

**Query params**:
| Param | Description |
|:---|:---|
| `token` | Auth token |
| `workspace` | Root path for the LSP server |

### Custom Workspace Configuration
You can override or add LSP configurations by creating a `.neurex/lsp.json` file in your workspace root.

**Example `.neurex/lsp.json`**:
```json
{
  "python": ["/usr/bin/python3", "-m", "pyright"],
  "custom-lang": ["custom-lsp-server", "--stdio"]
}
```
If a language is defined here, it takes precedence over both the native registry and system discovery.

### `GET /api/intelligence/ast-bounds`
Computes class, method, or function boundaries for target coordinates using the Tree-Sitter AST parser.

**Query params**:
| Param | Type | Description |
|:---|:---|:---|
| `path` | string | Relative path to the file |
| `line` | integer | 1-indexed line number |
| `column` | integer | 1-indexed column number |

**Response `200`**:
```json
{
  "start_line": 10,
  "end_line": 25
}
```

---

## Model Context Protocol (MCP) & Sandbox

Provides complete transparency and customization over the agent's active toolbox, allowing the visual configuration of execution rules per tool and manual payload playground runs.

### `GET /api/mcp/servers`
Lists core virtual servers and dynamic skill-based servers along with tools, input schemas, and granular permissions.

**Auth**: `developer`

**Response `200`**:
```json
[
  {
    "id": "filesystem-substrate",
    "name": "Filesystem Substrate",
    "status": "connected",
    "type": "core",
    "tools": [
      {
        "name": "read_file",
        "description": "Read the contents of a file",
        "inputSchema": {
          "type": "object",
          "properties": {
            "path": { "type": "string", "description": "Parameter path (string)" }
          },
          "required": ["path"]
        },
        "rule": "allow"
      }
    ]
  }
]
```

### `POST /api/mcp/permissions`
Updates the granular permission rule (`allow`, `ask`, `deny`) for a specific tool.

**Auth**: `developer`

**Body**:
```json
{
  "tool_name": "write_file",
  "rule": "allow"
}
```

**Response `200`**:
```json
{
  "status": "success",
  "tool_name": "write_file",
  "rule": "allow"
}
```

### `POST /api/mcp/playground/run`
Executes a tool manually within the user-steered playground, bypassing limited autonomy ceilings.

**Auth**: `developer`

**Body**:
```json
{
  "tool_name": "list_directory",
  "arguments": { "path": "." }
}
```

**Response `200`**:
```json
{
  "status": "success",
  "result": "..."
}
```

### `POST /api/mcp/servers/import`
Clones and registers a new MCP server from a Git repository or local subdirectory.

**Auth**: `admin`

**Body**:
```json
{
  "url": "https://github.com/example/mcp-server"
}
```

**Response `200`**:
```json
{
  "status": "success",
  "server_name": "mcp-server"
}
```

---

## Git & Version Control

Direct git management for the workspace.

### `GET /api/git/status`
Returns the current branch and porcelain status of the workspace.

### `GET /api/git/diff?path={path}`
Returns the diff between `HEAD` and the current disk state.

### `GET /api/git/blame?path={path}`
Returns line-by-line authorship information (Hash, Author, Summary, Time).

### `GET /api/git/history?path={path}`
Returns the commit history for a specific file.

### `POST /api/git/stage`
Stage a file (`git add`). Body: `{ "path": "string" }`.

### `POST /api/git/commit`
Commit staged changes. Body: `{ "message": "string" }`.

---

## Skills & Extensions

Skills are Python modules that extend agent capabilities. The Skills system is the foundation for Neurex's plugin architecture.

### `GET /api/skills/`
List all installed skills with their metadata and enabled state.

**Response `200`**:
```json
[
  {
    "id": "web-search",
    "name": "Web Search",
    "description": "DuckDuckGo search integration",
    "enabled": true,
    "version": "1.0.0"
  }
]
```

---

### `GET /api/skills/curated`
Returns the curated list of officially supported skills available for installation.

---

### `POST /api/skills/install`
Install a new skill by package name or Git URL.

**Auth**: `developer` or higher  
**Body**:
```json
{ "source": "git+https://github.com/example/neurex-skill-db.git", "name": "db-explorer" }
```

---

### `DELETE /api/skills/{skill_id}`
Uninstall a skill.

**Auth**: `developer` or higher

---

## Settings

### `GET /api/settings/`
Fetch current application settings (model selection, context window, autonomy ceiling, etc.).

**Auth**: Any role

---

### `POST /api/settings/`
Update settings. Partial update is supported. This endpoint is the source of truth for the **Dynamic Model Routing** substrate.

**Auth**: `admin`  
**Body** (example with routing):
```json
{
  "default_model": "qwen2.5-coder:32b",
  "autonomy_ceiling": "limited",
  "model_routes": {
    "Planning": "gpt-4o",
    "Coding": "qwen2.5-coder:32b",
    "Testing": "llama3.1:8b",
    "Reviewing": "claude-3-5-sonnet"
  }
}
```
> [!NOTE]
> The `model_routes` map allows overriding specific agent roles. If a role is missing, the orchestrator falls back to role-specific defaults or the `default_model`.

---

## Notifications

### `POST /api/notifications/register`
Register a Web Push subscription for mobile/browser push notifications (HITL approvals, agent alerts).

**Body**: Web Push `PushSubscription` JSON object

---

## Self-Update

### `GET /api/update/check`
Polls GitHub Releases and compares against running `NEUREX_VERSION`. Updates internal state.

**Response `200`**:
```json
{
  "current_version": "0.5.2",
  "latest_version": "0.2.0",
  "update_available": true,
  "update_ready": false,
  "pulling": false
}
```

---

### `GET /api/update/status`
Lightweight cached status poll (no external network call). Used by the frontend badge every 5s during active pulls.

---

### `POST /api/update/apply`
Trigger a background `docker compose pull` to download updated images. The service remains live until the user reloads.

**Auth**: `admin`

---

### `GET /api/update/backups`
List all available system snapshots (backups created before updates).

**Auth**: `admin`

---

### `POST /api/update/rollback/{name}`
Restore the system state from a specific snapshot.

**Auth**: `admin`

---

### `GET /api/observability/flight-log/{conversation_id}`
Retrieve the structured reasoning trace for a specific conversation.

**Auth**: `any`

---

### `GET /api/observability/replay/{conversation_id}`
Retrieve decision logs formatted as chronological screenplay beats for step-by-step agent telemetry.

**Response `200`**:
```json
[
  {
    "beat_number": 1,
    "timestamp": "2026-05-22T13:27:16.123456Z",
    "agent_type": "planner",
    "act": "Create Plan",
    "narrative": "Analyzing workspace structural health",
    "context_metadata": ["files", "git"]
  }
]
```

---

## WebSocket Protocol

**Endpoint**: `ws://localhost:8000/ws/{conversation_id}`

The WebSocket is the primary channel for all real-time agent interaction, terminal I/O, and swarm presence.

### Client → Server Messages

| `type` | Payload | Description |
|:---|:---|:---|
| `message` | `{ content: string }` | Send a user message to trigger agent orchestration |
| `approve_task` | `{ task_id: string }` | Approve a single HITL-gated task |
| `cancel_task` | `{ task_id: string }` | Cancel a pending task |
| `terminal_input` | `{ data: string }` | PTY stdin |
| `terminal_sync` | `{ cwd: string }` | **New**. Initialize/Sync PTY with directory anchoring |
| `terminal_resize` | `{ rows: int, cols: int }` | Resize PTY |

### Server → Client Messages

| `type` | Payload | Description |
|:---|:---|:---|
| `token` | `{ content: string }` | Streaming LLM token |
| `task_update` | `TaskNode` | Task status change |
| `plan_updated` | `{ graph_id }` | The execution graph was rewritten by The Commander |
| `approval_request` | `{ task_id, reason, command }` | HITL gate — agent is waiting |
| `terminal_output` | `{ data: string }` | PTY stdout |
| `presence_update` | `[{ user_id, status, cursor }]` | Swarm presence state |
| `error` | `{ detail: string }` | Server-side error |

---

## Error Reference

| HTTP Code | Meaning |
|:---|:---|
| `400` | Bad request / validation error |
| `401` | Missing or invalid JWT |
| `403` | Insufficient role (`require_role` dependency) |
| `404` | Resource not found |
| `500` | Unhandled server error (logged via structlog) |

**APPROVAL_REQUIRED** (string response, not HTTP error): Returned by the terminal and filesystem tools when `autonomy_ceiling` blocks auto-execution. The frontend should surface this as an approval prompt.

---

## Health Check

### `GET /health`
```json
{ "status": "ok", "version": "0.6.0" }
```
No authentication required.
