# ⬡ Neurex Hardware Benchmarks: LLM Tier List

This document provides a guide for selecting and ranking hardware for your Neurex compute mesh. Performance is measured primarily by **Inference Speed (Tokens per Second)** and **Memory Capacity (VRAM/Unified Memory)**.

---

## 🏆 Tier 1: The Hive Overlords (Elite)
*Best for: Running 70B+ models at interactive speeds or handling massive context windows.*

| Model | Architecture | VRAM / Memory | Why it wins |
|:---|:---|:---|:---|
| **NVIDIA RTX 4090** | Ada Lovelace | 24GB G6X | **Speed King**. Fastest consumer card for prefill and generation. CUDA is the most optimized backend. |
| **Apple M3/M4 Max/Ultra** | Apple Silicon | Up to 192GB | **Capacity King**. Unified memory allows running huge models (DeepSeek-R1 671B) that no single GPU can touch. |
| **NVIDIA RTX 3090 (Ti)** | Ampere | 24GB G6X | **Value King (Used)**. Matches 4090 in VRAM for much less money. Dual-link support for NVLink is a hidden gem. |

---

## 🥇 Tier 2: High-Speed Command Nodes
*Best for: Running 14B - 32B models at lightning speed or 70B models in a pooled mesh.*

| Model | Architecture | VRAM / Memory | Why it wins |
|:---|:---|:---|:---|
| **AMD RX 7900 XTX** | RDNA 3 | 24GB G6 | Great VRAM capacity. ROCm performance in `llama.cpp` is now highly competitive with NVIDIA. |
| **Apple M2/M3 Pro** | Apple Silicon | 18GB - 36GB | Efficient, quiet, and reliable. Great for standalone Master nodes. |
| **NVIDIA RTX 4080 (Super)** | Ada Lovelace | 16GB G6X | Incredible speed, though VRAM is slightly limited for larger models without pooling. |

---

## 🥈 Tier 3: Reliable Swarm Workers
*Best for: Serving as RPC Nodes to contribute VRAM to the mesh.*

| Model | Architecture | VRAM / Memory | Why it wins |
|:---|:---|:---|:---|
| **AMD RX 7900 XT** | RDNA 3 | 20GB G6 | Solid "middle ground" for VRAM. High bandwidth makes it a great RPC worker. |
| **Intel Arc A770** | Alchemist | 16GB G6 | **Budget Powerhouse**. 16GB of VRAM at this price point is unmatched. Vulkan/SYCL support is maturing. |
| **NVIDIA RTX 3060 (12GB)** | Ampere | 12GB G6 | The most affordable "entry level" card that can actually fit decent models. |

---

## 🥉 Tier 4: Edge Nodes
*Best for: Lightweight tasks, UI serving, or small 7B models.*

| Model | Architecture | VRAM / Memory | Why it wins |
|:---|:---|:---|:---|
| **NVIDIA RTX 4060 Ti (16GB)** | Ada Lovelace | 16GB G6 | Low power, high VRAM. Great for dedicated low-energy RPC workers. |
| **Apple M1/M2 (Base)** | Apple Silicon | 8GB - 16GB | Good for light development and UI oversight. |
| **NVIDIA RTX 4070 (Ti)** | Ada Lovelace | 12GB G6X | Fast, but the 12GB VRAM cap is the primary bottleneck for Neurex tasks. |

---

## ⬡ Pro-Tips for Mesh Building

1.  **Memory Bandwidth is King**: For token generation, bandwidth (GB/s) matters more than TFLOPS. This is why a 3090 often feels as fast as a 4090 for text.
2.  **The 24GB Sweet Spot**: The RTX 3090/4090 and 7900 XTX are the "Golden Tier" because they can fit a Q4_K_M quantized 30B model entirely in VRAM.
3.  **Mixing Nodes**: Neurex's **MeshRouter** intelligently offloads heavier math to NVIDIA nodes while using Apple nodes for large context storage.
4.  **Used Market**: A used RTX 3090 is currently the single best investment for a Neurex Master node.

---
*Last Updated: April 2025. Benchmarks based on llama.cpp (GGUF) performance.*
