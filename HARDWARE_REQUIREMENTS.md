# Neurex Hardware Infrastructure Requirements

Neurex is an Agentic Operating System designed for high-performance local inference. Because it operates a distributed mesh, hardware requirements vary depending on node roles.

## 1. Node Roles

### Master Node (The Brain)
- **CPU**: 8+ Cores (AVX2 support required)
- **RAM**: 32GB+ (64GB recommended for large codebases)
- **GPU**: NVIDIA RTX 3090/4090 (24GB VRAM) or Apple M2/M3 Max (64GB+ Unified Memory)
- **Storage**: 100GB+ NVMe SSD (for ChromaDB vector index)

### Worker Node (The Muscle)
- **CPU**: 4+ Cores
- **RAM**: 16GB+
- **GPU**: Any NVIDIA (8GB+ VRAM), AMD (ROCm), or Intel (SYCL)
- **Role**: Handles specific sub-tasks or redundant inference streams.

---

## 2. Docker vs. Native Deployment

### Linux (NVIDIA/AMD)
- **Docker Support**: Excellent. Requires `nvidia-container-toolkit`. 
- **GPU Sharing**: Supported. You can run Neurex on your primary display GPU. The Linux kernel will multiplex access.
- **Limitation**: High VRAM pressure may cause X11/Wayland lag if the model exceeds available memory.

### macOS (Apple Silicon)
- **Docker Support**: **NOT RECOMMENDED for Inference**. 
- **The Issue**: Docker Desktop on Mac cannot access the Metal (GPU) acceleration framework. 
- **Recommendation**: Run the Neurex API and Ollama **natively** on macOS. Use the `./neurex/neurex.sh` launcher outside of Docker for maximum performance.

### Windows (WSL2)
- **Docker Support**: Good (via Docker Desktop for Windows).
- **GPU Sharing**: Supported via WSL2's native GPU abstraction.
- **Limitation**: Higher overhead than native Linux.

---

## 3. GPU Passthrough & "Only GPU" Scenarios

If you have a **Single GPU system**:
1. **Linux**: Neurex will share the GPU with your desktop. Ensure you have enough VRAM to headroom for your UI (usually ~1-2GB).
2. **Persistence**: In Docker, use the `deploy.resources.reservations` section in `docker-compose.yml`.
3. **Multi-GPU**: Neurex can be configured to use specific GPUs (e.g., GPU 0 for display, GPU 1 for Neurex) by setting `NVIDIA_VISIBLE_DEVICES` in the environment.

---

## 4. Performance Tuning

- **ChromaDB**: The initial scan of a massive repository (>10,000 files) will use high I/O. Use an NVMe drive to prevent UI lag.
- **Context Pinning**: Pinning large files to context uses VRAM. Monitor the **Infra Hub** gauges to prevent OOM (Out of Memory) crashes.
