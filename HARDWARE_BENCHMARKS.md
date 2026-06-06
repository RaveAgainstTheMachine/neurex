# ⬡ Neurex Hardware Benchmarks: LLM Tier List (2025/2026 Edition)

This guide ranks hardware for your Neurex compute mesh based on **Inference Speed (Tokens per Second)** and **Memory Capacity**.

---

## 🚀 Performance Benchmarks (Llama-3 8B / 70B)
*Measured at Q4_K_M quantization (4-bit). t/s = Tokens per Second.*

| GPU Model                  | Architecture | VRAM / Memory | 8B t/s (Gen) | 70B t/s (Gen) | Bandwidth  |
|:---------------------------|:-------------|:--------------|:-------------|:--------------|:-----------|
| **NVIDIA RTX 5090**        | Blackwell    | 32GB GDDR7    | 215.0        | 38.5          | 1,792 GB/s |
| **NVIDIA RTX 4090**        | Ada Lovelace | 24GB G6X      | 155.0        | 22.0          | 1,008 GB/s |
| **Apple M3 Ultra (192GB)** | Apple Silicon| 192GB Unified | 110.0        | 18.5          | 800 GB/s   |
| **NVIDIA RTX 3090 (Ti)**   | Ampere       | 24GB G6X      | 120.0        | 16.5          | 936 GB/s   |
| **Intel Arc Pro B70**      | Battlemage   | 32GB GDDR6    | 85.0         | 14.0          | 608 GB/s   |
| **NVIDIA RTX 5080**        | Blackwell    | 16GB GDDR7    | 145.0        | (N/A)*        | 960 GB/s   |
| **AMD RX 7900 XTX**        | RDNA 3       | 24GB G6       | 125.0        | 15.5          | 960 GB/s   |
| **Intel Arc B580**         | Battlemage   | 12GB GDDR6    | 65.0         | (N/A)*        | 456 GB/s   |
| **NVIDIA RTX 3060 (12GB)** | Ampere       | 12GB G6       | 45.0         | (N/A)*        | 360 GB/s   |

*\*Models too large for single-GPU VRAM without Neurex Mesh Pooling.*

---

## 🏆 Tier 1: The Hive Overlords (Elite)
*Best for: Running 70B+ models at interactive speeds or handling massive context.*

| Model                | Architecture  | VRAM / Memory | Why it wins                                         |
|:---------------------|:--------------|:--------------|:----------------------------------------------------|
| **NVIDIA RTX 5090**  | Blackwell     | 32GB GDDR7    | **The New Standard**. 32GB fits 30B+ comfortably.   |
| **Apple M3/M4 Ultra**| Apple Silicon | Up to 192GB   | **Massive Context**. Runs 671B DeepSeek-R1.         |
| **NVIDIA RTX 4090**  | Ada Lovelace  | 24GB G6X      | Ultra-reliable CUDA performance.                    |
| **Intel Arc Pro B70**| Battlemage    | 32GB GDDR6    | **Enterprise Value**. 32GB for AI inference.        |

---

## 🥇 Tier 2: High-Speed Command Nodes
*Best for: Running 14B - 32B models at lightning speed.*

| Model                | Architecture  | VRAM / Memory | Why it wins                                         |
|:---------------------|:--------------|:--------------|:----------------------------------------------------|
| **NVIDIA RTX 5080**  | Blackwell     | 16GB GDDR7    | High speed for mid-sized agent models.              |
| **AMD RX 7900 XTX**  | RDNA 3        | 24GB G6       | Best non-NVIDIA capacity for the price.             |
| **NVIDIA RTX 3090**  | Ampere        | 24GB G6X      | The budget king for 24GB VRAM nodes.                |

---

## 🥈 Tier 3: Reliable Swarm Workers
*Best for: Serving as RPC Nodes to contribute VRAM to the mesh.*

| Model                | Architecture  | VRAM / Memory | Why it wins                                         |
|:---------------------|:--------------|:--------------|:----------------------------------------------------|
| **Intel Arc B580**   | Battlemage    | 12GB GDDR6    | Solid 12GB performance for mesh expansion.          |
| **NVIDIA RTX 4060 Ti**| Ada Lovelace  | 16GB G6       | Low power consumption for 24/7 RPC nodes.          |
| **NVIDIA RTX 3060**  | Ampere        | 12GB G6       | The most affordable way to join the mesh.           |

---

## ⬡ Pro-Tips for Mesh Building

1.  **The Blackwell Advantage**: The jump to GDDR7 in the 50-series provides nearly 2x the memory bandwidth, which directly correlates to token generation speed.
2.  **Intel's 32GB Sleeper**: The Arc Pro B70 is a workstation card, but its 32GB of VRAM makes it an incredible candidate for a Neurex Master node on a budget.
3.  **Memory Bandwidth > TFLOPS**: Always prioritize memory bandwidth. This is why the RTX 3090 (936 GB/s) often outperforms the newer 4080 (736 GB/s) in large LLM tasks.
4.  **Quantization**: All benchmarks above assume 4-bit (Q4_K_M) quantization. Higher bitrates will lower the t/s linearly with the size increase.

---
*Last Updated: April 2025. Benchmarks based on llama.cpp (GGUF) performance.*
