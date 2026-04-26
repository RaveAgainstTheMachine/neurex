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

---

## ⚖️ 2026 Performance Status

| Category             | Cloud Standard | Neurex Rival (Local) | Verdict |
|:---------------------|:---------------|:---------------------|:--------|
| **Deep Thinking**    | **OpenAI o3**  | **DeepSeek-R1**      | **Tie**. R1 is superior for open coding. |
| **Coding Precision** | **Claude 4.0** | **Qwen-2.5-Coder**   | **OS Wins**. Local FIM is faster. |
| **Multi-Modal**      | **Gemini 2.0** | **Llama 3.2 + LTX**  | **Parity**. Local has no privacy leak. |

---
*Last Updated: April 2026. Benchmarks based on SWE-bench Pro and Terminal-Bench 2.0.*

