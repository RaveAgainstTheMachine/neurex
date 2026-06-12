# Neurex Installation Guide

This guide provides a comprehensive walkthrough for setting up Neurex v0.14.10 across different operating systems. Neurex is a high-performance, autonomous engineering workspace that requires specific hardware and software substrates to function at peak capacity.

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

## 🚀 Installation Methods

### Method 1: The One-Click CLI Binary

Download the pre-compiled `neurex` binary for your platform from the GitHub Releases. The CLI binary embeds the entire frontend and orchestrates containerized API services.

#### 🐧 Linux (x86_64)
```bash
# Move to a directory in your PATH and make executable
sudo mv neurex-linux-x86_64 /usr/local/bin/neurex
chmod +x /usr/local/bin/neurex

# Start the substrate
neurex start
```

#### 🍏 macOS (M1/M2/M3/M4 & Intel)
The release asset `neurex-macos-universal` is a raw CLI binary compiled for macOS. Because it is downloaded via the web and not signed by an Apple Developer profile, macOS Gatekeeper blocks it by default.
Run these commands in Terminal to register and run the binary:
```bash
# 1. Make the binary executable
chmod +x neurex-macos-universal

# 2. Strip Apple quarantine flags
xattr -d com.apple.quarantine neurex-macos-universal

# 3. Move to path (optional)
sudo mv neurex-macos-universal /usr/local/bin/neurex

# 4. Start the substrate
neurex start
```

#### 🏁 Windows 11+ (via WSL2)
Download `neurex-windows-x86_64.exe` inside your WSL2 environment, make it executable, and run:
```bash
chmod +x neurex-windows-x86_64.exe
./neurex-windows-x86_64.exe start
```

---

### Method 2: Unified Bootstrap Installer (Recommended)

Neurex features an interactive bootstrap installer that automatically verifies, configures, and installs system-level dependencies (Git, Docker, and GPU container runtimes) for your host platform.

```bash
git clone https://github.com/RaveAgainstTheMachine/neurex.git
cd neurex
./install.sh
```

#### OS Dependency Handling:
- **Linux (Ubuntu/Debian)**: Automatically installs Git, Docker, Docker Compose, and registers the NVIDIA Container Toolkit runtime on system GPUs.
- **macOS**: Prompts to auto-install missing tools using Homebrew (`brew`).
- **Windows (WSL2)**: Integrates with Windows host CLI, executing `winget` from WSL2 to install Docker Desktop on the host.

---

## 🐧 OS-Specific Setup Details

### Linux Setup

#### Ubuntu / Debian / Pop!_OS (Manual)
1. **Docker Setup**:
    ```bash
    sudo apt-get update
    sudo apt-get install docker-ce docker-ce-cli containerd.io docker-compose-plugin
    sudo usermod -aG docker $USER
    ```

#### Arch Linux / EndeavourOS / Manjaro (Manual)
1. **Docker Setup**:
    ```bash
    sudo pacman -S docker docker-compose
    sudo systemctl enable --now docker
    sudo usermod -aG docker $USER
    ```

#### GPU Acceleration (NVIDIA)
Ensure the [NVIDIA Container Toolkit](https://docs.nvidia.com/datacenter/cloud-native/container-toolkit/latest/install-guide.html) is installed to allow Docker containers access to hardware VRAM.

#### Firewall (UFW)
Neurex requires ports `3000` (Web UI) and `8000` (API) to be open.
```bash
sudo ufw allow 3000/tcp
sudo ufw allow 8000/tcp
```

### Windows (WSL2)
> [!CAUTION]
> Do NOT run Neurex natively on Windows Command Prompt or PowerShell for production. Performance and sandboxing are significantly better inside **WSL2**.

1. **Enable WSL2**: `wsl --install`
2. **Docker Desktop**: Install [Docker Desktop for Windows](https://www.docker.com/products/docker-desktop/) and enable the WSL2 integration in Settings.
3. **NVIDIA Drivers**: Ensure you have the latest NVIDIA drivers installed on the Windows host; WSL2 automatically bridges them.

### macOS (Intel & M-Series)
1. **Docker Desktop**: Install [Docker Desktop for Mac](https://www.docker.com/products/docker-desktop/).
2. **Metal Acceleration**: Apple M-Series chips are supported natively for fast local model inference via Metal Performance Shaders (MPS).

---

## 🛠️ Troubleshooting

### "Docker Daemon NOT Detected"
Ensure Docker is running. On Linux, run `sudo chmod 666 /var/run/docker.sock` (not recommended for production) or restart your terminal session to apply the `usermod` group changes.

### "VRAM Allocation Failed"
If your GPU runs out of memory, reduce the `OLLAMA_NUM_PARALLEL` variable in your `.env` file or choose a smaller model size (e.g. 7B instead of 14B).

### "mTLS Handshake Error"
If mTLS was enabled during installation, you must import the generated `neurex-internal-ca.crt` file into your system browser's trust store to access the dashboard.

---

## 🌐 Mesh Federation (Optional)

To link multiple machines into a single VRAM pool:
1. Install Neurex as a **Node** on the secondary machine using `install.sh`.
2. Provide the IP/Domain of your **Master** node.
3. The Master will automatically discover the new Node and add its VRAM to the collective pool.

---

<div align="center">
  <sub>For advanced configuration, see the [[API-Reference]].</sub>
</div>
