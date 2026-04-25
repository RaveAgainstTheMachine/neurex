# Neurex Enterprise: Hardware Requirements Specification

Neurex is a highly modular platform. Its performance footprint depends entirely on how you configure your local LLM engines and distributed mesh.

## Tier 1: Minimum (The "Scout" Setup)
*Designed for basic coding assistance, API-delegated inference (OpenAI/Anthropic proxy), or acting as a lightweight Mesh Worker node.*
*   **CPU**: 4-Core Processor (Intel i5 8th Gen or equivalent)
*   **RAM**: 8 GB DDR4
*   **GPU**: None required (CPU inference for small models like Qwen-1.5B)
*   **Storage**: 20 GB SSD (for application, logs, and a single lightweight model)
*   **Network**: 100 Mbps (for mesh synchronization)
*   **Capabilities**: Can run the Orchestrator, stream remote models, and participate in low-tier distributed CPU inference.

## Tier 2: Recommended (The "Developer" Setup)
*Designed for fully autonomous local agentic workflows, fast code completion, and running mid-sized models (8B - 14B parameters).*
*   **CPU**: 8-Core Processor (Apple Silicon M1/M2/M3, AMD Ryzen 7, or Intel i7)
*   **RAM**: 32 GB DDR5 (Critical for large context windows)
*   **GPU**: Nvidia RTX 3060/4060 (12GB VRAM) OR Apple Unified Memory
*   **Storage**: 100 GB NVMe SSD (for multiple quantized models)
*   **Network**: Gigabit LAN (for fast Mesh file/tensor transfer)
*   **Capabilities**: Full autonomous agent execution, local RAG document embeddings, fast inference at 30+ tokens/second.

## Tier 3: "I'm Rich!" (The "Nexus" Setup)
*Designed for hosting the entire Mesh brain locally, running 70B+ parameter models at lightning speed, and commanding multiple agent swarms simultaneously.*
*   **CPU**: 32+ Core HEDT (AMD Threadripper or Dual EPYC/Xeon)
*   **RAM**: 256 GB+ ECC DDR5
*   **GPU**: 4x Nvidia RTX 4090 (96GB total VRAM) OR Apple Mac Studio M2 Ultra (192GB Unified Memory)
*   **Storage**: 2 TB PCIe Gen 5 NVMe SSD (for unquantized models and massive workspace indexing)
*   **Network**: 10 Gigabit Fiber/Ethernet (for zero-latency distributed MPI inference across the Mesh)
*   **Capabilities**: Instantaneous parallel agent swarms, local fine-tuning, running state-of-the-art models (Llama-3-70B, Command-R+) at full precision.
