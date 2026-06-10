# Neurex Installation Guide

This guide provides a comprehensive walkthrough for setting up Neurex v0.14.8 across different operating systems. Neurex is a high-performance, autonomous engineering workspace that requires specific hardware and software substrates to function at peak capacity.

---

## 🖥️ System Requirements

### Hardware Tiers

| Component | Minimum (Restricted) | Recommended (Autonomous) |
| :--- | :--- | :--- |
| **CPU** | 4 Cores (AVX2 support) | 8+ Cores (AVX512 preferred) |
| **RAM** | 16 GB | 32 GB - 128 GB |
| **GPU** | CPU-only | NVIDIA (RTX/Tesla/Quadro), AMD (Radeon/Instinct), Intel (Arc), or Apple M-Series |
| **Storage** | 20 GB SSD | 500 GB+ NVMe (for model storage) |
| **Network** | Localhost only | 1 Gbps LAN (for Mesh Federation) |

> [!IMPORTANT]
> Local LLM inference is extremely memory-intensive. For a smooth experience with models like Qwen-2.5-Coder (14B/32B), a dedicated GPU with at least 12GB of VRAM is highly recommended. Neurex supports hardware acceleration on NVIDIA (CUDA), AMD (ROCm), Intel (oneAPI), and Apple Silicon (MPS).

---

## 🚀 Unified Installation Method

Neurex features an interactive bootstrap installer that automatically verifies, configures, and installs system-level dependencies (Git, Docker, and GPU container drivers) for your host platform.

### Run the Installer

Clone the repository and launch the installer script:

```bash
git clone https://github.com/RaveAgainstTheMachine/neurex.git
cd neurex
./install.sh
```

The installer detects your operating system, active GPUs, and prompts you to install missing components automatically:
- **Linux (Ubuntu/Debian)**: Installs Git, Docker, Docker Compose, and configures NVIDIA Container Toolkit runtimes automatically.
- **macOS (M1+)**: Prompts to install Git and Docker via Homebrew.
- **Windows 11+ (WSL2)**: Integrates with the host system, launching `winget` directly from inside WSL2 to install Docker Desktop on Windows.

---

## 🐧 OS-Specific Setup

### Linux Setup

#### Ubuntu / Debian / Pop!_OS
1.  **Docker Setup**:
    ```bash
    sudo apt-get update
    sudo apt-get install docker-ce docker-ce-cli containerd.io docker-compose-plugin
    sudo usermod -aG docker $USER
    ```

#### Arch Linux / EndeavourOS / Manjaro
1.  **Docker Setup**:
    ```bash
    sudo pacman -S docker docker-compose
    sudo systemctl enable --now docker
    sudo usermod -aG docker $USER
    ```

#### GPU Acceleration (NVIDIA)
Install the [NVIDIA Container Toolkit](https://docs.nvidia.com/datacenter/cloud-native/container-toolkit/latest/install-guide.html) to allow Docker to access your GPU.

#### Firewall (UFW)
Neurex requires ports `3000` (Web) and `8000` (API) to be open for LAN access.
```bash
sudo ufw allow 3000/tcp
sudo ufw allow 8000/tcp
```

### Windows (WSL2)

> [!CAUTION]
> Do NOT run Neurex natively on Windows Command Prompt or PowerShell for production. Performance and sandboxing are significantly better inside **WSL2**.

1.  **Enable WSL2**: `wsl --install`
2.  **Docker Desktop**: Install [Docker Desktop for Windows](https://www.docker.com/products/docker-desktop/) and enable the WSL2 integration in Settings.
3.  **NVIDIA Drivers**: Ensure you have the latest NVIDIA Game Ready or Studio drivers installed on the Windows host; WSL2 will automatically detect them.

### macOS (Intel & M-Series)

1.  **Docker Desktop**: Install [Docker Desktop for Mac](https://www.docker.com/products/docker-desktop/).
2.  **Metal Acceleration**: Neurex leverages Apple's Metal Performance Shaders (MPS). M1/M2/M3 chips are natively supported for high-speed inference without additional drivers.

---

## 🛠️ Troubleshooting

### "Docker Daemon NOT Detected"
Ensure Docker is running and your user has permissions. On Linux, try `sudo chmod 666 /var/run/docker.sock` (not recommended for production) or ensure you've performed the `usermod` step above.

### "VRAM Allocation Failed"
If your GPU is running out of memory, reduce the `OLLAMA_NUM_PARALLEL` environment variable in your `.env` file or switch to a smaller quantized model (e.g., 7B instead of 14B).

### "mTLS Handshake Error"
If you enabled mTLS in the installer, you must install the `neurex-internal-ca.crt` in your browser's trust store to access the Web UI.

---

## 🌐 Mesh Federation (Optional)

To link multiple machines into a single VRAM pool:
1.  Install Neurex as a **Node** on the secondary machine using `install.sh`.
2.  Provide the IP/Domain of your **Master** node.
3.  The Master will automatically discover the new Node and add its VRAM to the collective pool.

---

<div align="center">
  <sub>For advanced configuration, see the [[API-Reference]].</sub>
</div>
