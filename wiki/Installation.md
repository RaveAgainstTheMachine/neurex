# Neurex Installation Guide

This guide provides a comprehensive walkthrough for setting up Neurex v0.5.2 across different operating systems. Neurex is a high-performance, autonomous engineering workspace that requires specific hardware and software substrates to function at peak capacity.

---

## 🖥️ System Requirements

### Hardware Tiers

| Component | Minimum (Restricted) | Recommended (Autonomous) |
| :--- | :--- | :--- |
| **CPU** | 4 Cores (AVX2 support) | 8+ Cores (AVX512 preferred) |
| **RAM** | 16 GB | 32 GB - 128 GB |
| **GPU** | No dedicated GPU (CPU-only) | NVIDIA RTX (8GB+ VRAM) or Apple M-Series |
| **Storage** | 20 GB SSD | 500 GB+ NVMe (for model storage) |
| **Network** | Localhost only | 1 Gbps LAN (for Mesh Federation) |

> [!IMPORTANT]
> Local LLM inference is extremely memory-intensive. For a smooth experience with models like Qwen-2.5-Coder (14B/32B), a dedicated GPU with at least 12GB of VRAM is highly recommended.

---

## 📦 Software Prerequisites

Before installing Neurex, ensure the following are installed on your host system:

1.  **Docker & Docker Compose**: The primary substrate for sandboxing and containerized services.
2.  **Git**: Required for cloning the repository and managing your neural mesh projects.
3.  **Python 3.11+**: Used for the bootstrap installer and auxiliary tools.
4.  **NVIDIA Container Toolkit** (Linux/Windows only): Required for GPU-accelerated inference within Docker.

---

## 🚀 Installation Methods

### Method 1: The One-Click Binary (Recommended)
This is the fastest way to get started. Download the pre-compiled `neurex` binary for your platform from the [GitHub Releases](https://github.com/RaveAgainstTheMachine/neurex/releases).

```bash
# Move to a directory in your PATH
sudo mv neurex-linux-x86_64 /usr/local/bin/neurex
chmod +x /usr/local/bin/neurex

# Start the substrate
neurex start
```

### Method 2: Docker Full-Stack (Self-Hosted)
Best for production environments or if you want to run the full suite (API, Web, Mesh) via Docker Compose.

```bash
git clone https://github.com/RaveAgainstTheMachine/neurex.git
cd neurex
./install.sh
```

---

## 🐧 OS-Specific Setup

### Linux (Ubuntu / Arch / Debian)

1.  **Docker Setup**:
    ```bash
    sudo apt-get update
    sudo apt-get install docker-ce docker-ce-cli containerd.io docker-compose-plugin
    sudo usermod -aG docker $USER
    ```
2.  **GPU Acceleration (NVIDIA)**:
    Install the [NVIDIA Container Toolkit](https://docs.nvidia.com/datacenter/cloud-native/container-toolkit/latest/install-guide.html) to allow Docker to access your GPU.
3.  **Firewall (UFW)**:
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
