# Hardware Acceleration

Neurex is built for high-throughput inference on local hardware. The **Universal Installer** automatically detects and configures the optimal acceleration backend.

## 1. Supported Backends
- **Apple Silicon (Metal)**: Fully optimized for M1/M2/M3 chips.
- **Nvidia (CUDA)**: Standard acceleration for RTX/Quadro GPUs.
- **AMD (ROCm)**: Support for Radeon and Instinct hardware.
- **Intel (SYCL/OpenCL)**: Support for Arc and Data Center GPUs.

## 2. Detection Logic
The `install.sh` and `install.py` scripts perform deep hardware inspection:
- Checks for `/dev/dri/renderD128` (Linux/AMD).
- Parses `system_profiler` output (macOS).
- Identifies driver versions and VRAM availability.

## 3. Performance Monitoring
The **Infrastructure Hub** provides real-time telemetry:
- **Tokens Per Second (TPS)**: Live benchmarking of active models.
- **VRAM Utilization**: Visual indicators for memory pressure.
- **Load Balancing**: Automatically offloads tasks to peer nodes if local VRAM is exhausted.

## 4. Configuration
Backends can be toggled in the `SettingsPanel`. Ensure you have the appropriate drivers installed (e.g., `mesa-vulkan-radeon` on Linux for AMD).
