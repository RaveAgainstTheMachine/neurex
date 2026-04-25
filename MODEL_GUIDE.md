# ⬡ Neurex Model Guide: Latest & Greatest (2025/2026)

This guide ranks the best-performing Open Source models for local engineering tasks, sorted by **Single-GPU VRAM requirements** at **Q4_K_M (4-bit)** quantization.

---

## 🛠️ Model Inventory (Sorted by VRAM)

| Model Name             | Size | VRAM (Q4_K_M) | Primary Strength                  | Recommended GPU     |
|:-----------------------|:-----|:--------------|:----------------------------------|:--------------------|
| **Llama-3.2 1B/3B**    | 3B   | **~2.5 GB**   | Edge tasks, fast summarization.   | Any (Entry Level)   |
| **Phi-4 (Mini)**       | 4B   | **~3.2 GB**   | Logic, math, tool use.            | 4GB+ (Steam Deck)   |
| **DeepSeek-R1 (Dist)** | 7B   | **~5.1 GB**   | Elite reasoning & COT.            | 6GB (RTX 3060)      |
| **Qwen-2.5-Coder**     | 7B   | **~5.2 GB**   | High-speed technical generation.  | 6GB (RTX 3060)      |
| **Llama-3.1**          | 8B   | **~5.8 GB**   | General-purpose assistant.        | 8GB (RTX 4060)      |
| **Gemma-2**            | 9B   | **~6.5 GB**   | Creative writing & instructions.  | 8GB (RTX 4060)      |
| **Mistral NeMo**       | 12B  | **~8.1 GB**   | Balanced chat & context (128k).   | 12GB (RTX 3060)     |
| **Qwen-2.5-Coder**     | 14B  | **~9.5 GB**   | **Neurex Sweet Spot**. Pro coding. | 12GB (RTX 4070)     |
| **DeepSeek-R1 (Dist)** | 14B  | **~10.2 GB**  | Complex reasoning on mid-tier.    | 12GB (RTX 4070)     |
| **Codestral-22B**      | 22B  | **~14.5 GB**  | Dedicated coding (FIM expert).    | 16GB (RTX 4080)     |
| **Gemma-2**            | 27B  | **~17.8 GB**  | Elite-tier general instruction.   | 20GB+ (7900 XT)     |
| **Qwen-2.5-Coder**     | 32B  | **~20.1 GB**  | **Single-GPU King**. Best overall. | 24GB (3090/4090)    |
| **DeepSeek-R1 (Dist)** | 32B  | **~21.5 GB**  | Maximum reasoning (Single GPU).   | 24GB (3090/4090)    |
| **Llama-3.1**          | 70B  | **~42.0 GB**  | **Federated Only**. Best for Mesh. | Multi-GPU / Mesh    |
| **DeepSeek-R1 (Full)** | 671B | **~400 GB+**  | **Apple Silicon Ultra / Mesh**.   | M3/M4 Max/Ultra     |

---

## ⬡ Neurex Model Strategies

### 1. The "Sweet Spot" (12GB - 16GB VRAM)
If you have a mid-range card (RTX 3060 12GB / 4070), your best experience will be with **Qwen-2.5-Coder 14B**. It provides nearly 70B-tier coding performance while leaving enough VRAM for a healthy KV cache (context window).

### 2. The "Power User" (24GB VRAM)
With an RTX 3090/4090/5090, you should default to **Qwen-2.5-Coder 32B**. This is currently the gold standard for local engineering, capable of handling complex repo-level refactors entirely in VRAM.

### 3. The "Reasoning Swarm"
For tasks requiring deep logical chains (debugging complex race conditions or architecting new systems), use the **DeepSeek-R1 Distillations**. They use "Chain of Thought" (CoT) to think before they act, resulting in much higher success rates for the Neurex Planner agent.

### 4. The "Mesh Heavyweight"
If you have pooled multiple GPUs across your network, **Llama-3.1 70B** is your target. It is the only model that truly feels like "GPT-4" while running locally on consumer hardware.

---
*Last Updated: April 2025. Quantizations based on GGUF (Q4_K_M).*
