# Infrastructure Hub & NOC

The Neurex Infrastructure Hub serves as the **Network Operations Center (NOC)** for the neural substrate. It provides real-time oversight of the physical and virtual assets powering the agentic swarm.

## 1. The Infrastructure Dashboard
Access the dashboard via the **Activity Bar** (Infrastructure tab) or the **Substrate Launcher**. The dashboard provides a unified view of the entire Mesh topology.

### Node Monitoring
Each card in the dashboard represents a compute node (Local or Peer):
- **Resource Pools**: Real-time aggregation of CPU, RAM, VRAM, and Disk usage.
- **Storage Health**: Visual indicators of the health and accessibility of configured storage paths (e.g., `models_dir`, `neurex_install_dir`).
- **Hardware Telemetry**: Real-time discovery and display of CPU (model/cores) and GPU (model/VRAM) specifications.
- **Model Inventory**: A per-node list of installed and active models.

### Hardware High-Density View
Node cards use a **Spec Column** architecture that merges hardware identifiers with their corresponding metrics:
- **CPU Column**: Unified display of CPU Model and Core Count.
- **GPU Column**: Unified display of GPU Model and VRAM Capacity.
This architecture eliminates the need for tooltips and provides instant compute capacity assessment.

## 2. Model Operational States
Neurex distinguishes between the static presence of a model and its runtime readiness:

### 🔥 Hot (Active)
- **Definition**: The model is currently loaded into an inference engine (e.g., Ollama, vLLM) and occupying VRAM.
- **Visual**: Indicated by a pulsating **ACTIVE** dot and high-contrast styling in the catalog.
- **Telemetry**: Detected via live process monitoring (`/api/ps`).

### ❄️ Cold (Installed)
- **Definition**: The model weights are present on disk but the model is not currently running.
- **Visual**: Marked as **LOCAL** but without the active indicator.
- **Telemetry**: Detected via filesystem manifests and engine tags (`/api/tags`).

## 3. Storage Substrate
Neurex uses a path-aware telemetry system to monitor storage across multi-disk environments.

### Configurable Paths
Managed via **Settings > Workspace > Storage & Paths**:
- **Install Path**: The root directory for Neurex system files and logs.
- **Models Path**: The directory where LLM weights are stored (default: `~/.ollama/models`).
- **Telemetry Paths**: A list of directories that the system monitors for disk usage metrics.

### Health Gating
The system performs continuous permission checks on these paths:
- **Existence**: Verifies the directory exists.
- **Write Access**: Verifies Neurex has the permissions required for model deployment and log rotation.
- **Status**: Displayed as `OK` or `ERROR` (with path details) in the Dashboard.

## 4. Model Catalog & Deployment
The catalog reconciles multiple telemetry streams into a single, deduplicated view:
1. **Local Assets**: Prioritized over all other sources.
2. **Mesh Peers**: Models available for RPC/distributed inference on other nodes.
3. **Hugging Face**: Global discovery layer for new model acquisition.

### Smart Deployment
- **Deduplication**: If a model is already installed locally, the "Deploy" button is hidden to prevent redundant pulls.
- **Engine Awareness**: The system automatically detects if the required inference engine (e.g., Ollama) is offline and provides one-click recovery hints.

## 5. Dynamic Model Routing
Introduced in Phase 61, **Dynamic Model Routing** decouples the Orchestrator's cognitive roles from static model assignments.

### Cognitive Role Mapping
Users can bind specific agent personas to optimal models:
- **Planning**: Assigned to high-reasoning models (e.g., GPT-4o, Llama-3-70B).
- **Coding**: Assigned to specialized code generation models (e.g., Qwen2.5-Coder).
- **Testing/Reviewing**: Assigned to rapid-inference or specific validation models.

### The Routing Grid
The **InfraPanel** features a high-density grid for managing these mappings:
- **Role Assignment**: Click any role card to swap its model binding on the fly.
- **Custom Roles**: The "Add Role" affordance allows for the creation of proprietary cognitive targets.
- **Smart Fallbacks**: If a specific route is missing, the substrate automatically falls back to the global `default_model`, ensuring zero-latency execution.
