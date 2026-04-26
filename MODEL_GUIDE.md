# ⬡ Neurex Model Guide: Best-in-Class Agents (2026)

This guide highlights the elite open-source models integrated into Neurex, categorized by agent role and hardware requirements.

---

## 🛠️ Elite Model Registry

| Agent Type | Recommended Model | Engine | VRAM Req | Primary Strength |
|:-----------|:------------------|:-------|:---------|:-----------------|
| **Thinking** | **DeepSeek-R1 (32B)** | Ollama | **~20 GB** | Complex logic, deep reasoning, and COT. |
| **Coding**   | **Qwen-2.5-Coder (32B)** | Ollama | **~20 GB** | State-of-the-art repo-level engineering. |
| **Vision**   | **Llama-3.2-Vision (11B)** | Ollama | **~8.5 GB** | UI audits, image analysis, and OCR. |
| **Audio**    | **Whisper-Large-V3-Turbo** | Ollama | **~4.0 GB** | Real-time transcription & voice commands. |
| **Video**    | **LTX-Video** | vLLM | **~24.0 GB** | Video generation and frame-by-frame analysis. |
| **Images**   | **Stable-Diffusion-3.5** | vLLM | **~12.0 GB** | High-fidelity asset generation. |

---

## ⬡ Neurex Infrastructure Strategies

### 1. The Single-GPU Master (24GB VRAM)
If you have an RTX 3090/4090, your "Gold Stack" is:
*   **Primary Logic**: `DeepSeek-R1-32B`
*   **Coding Specialist**: `Qwen-2.5-Coder-32B`
Neurex will automatically swap these in/out of VRAM as needed, or run them concurrently if memory allows.

### 2. The Mesh Swarm (Distributed)
Neurex is designed for **Infra-Aware Inference**. If you enable **Mesh Routing**, you can split the load:
*   **Node A**: Handles Vision & Audio (Llama-3.2 + Whisper)
*   **Node B**: Handles heavy Coding tasks (Qwen-32B)
*   **Node C**: Handles Reasoning (DeepSeek-R1)

### 3. Hugging Face Integration
Neurex now supports direct searching and pulling from Hugging Face. Use the **Infrastructure Hub** to search for any GGUF or Ollama-compatible model. Neurex will estimate the VRAM requirements and recommend a suitable engine.

## ⬡ Neurex Infrastructure Hub

The Infrastructure Hub provides a real-time overview of your local and mesh-based compute resources.

### 1. Agent Recommendations
Neurex now features a dedicated section that maps elite models to specific agent roles:
*   **Logic (Thinking)**: `DeepSeek-R1` (32B+ recommended)
*   **Coding**: `Qwen-2.5-Coder` (32B recommended)
*   **Vision**: `Llama-3.2-Vision` (11B)
*   **Multimedia**: `Whisper` (Audio) and `LTX` (Video)

Each recommendation displays the **Parameter Count** and **VRAM Requirement** to help you match models to your hardware.

### 2. Verified Engine Monitoring
The status of engines like **Ollama** is now verified via both process detection and active API pings. If an engine shows as "STOPPED", ensure the service is active and the `ollama_base_url` in Settings is correct.

### 3. Model Discovery
Use the search bar to discover any GGUF or Ollama-compatible model from **Hugging Face**. Neurex will automatically estimate VRAM requirements and recommend a suitable engine.

---
*Last Updated: April 2026. Benchmarks based on SWE-bench Pro and Terminal-Bench 2.0.*

