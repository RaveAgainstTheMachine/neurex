use anyhow::{Result, bail};
use colored::*;
use std::io::{self, Write};
use std::process::Command;
use tracing::{error, info, warn};

#[allow(dead_code)]
pub enum HardwareType {
    Nvidia,
    Amd,
    Intel,
    AppleSilicon,
    Unknown,
}

pub struct SystemProfile {
    pub os: String,
    pub arch: String,
    pub gpu: HardwareType,
}

pub fn detect_profile() -> SystemProfile {
    let os = std::env::consts::OS.to_string();
    let arch = std::env::consts::ARCH.to_string();

    let mut gpu = HardwareType::Unknown;

    #[cfg(target_os = "linux")]
    {
        let lspci = Command::new("lspci").output();
        if let Ok(out) = lspci {
            let s = String::from_utf8_lossy(&out.stdout).to_lowercase();
            if s.contains("nvidia") {
                gpu = HardwareType::Nvidia;
            } else if s.contains("amd") || s.contains("radeon") {
                gpu = HardwareType::Amd;
            } else if s.contains("intel") {
                gpu = HardwareType::Intel;
            }
        }
    }

    #[cfg(target_os = "macos")]
    {
        let sysctl = Command::new("sysctl").arg("-n").arg("hw.optional.arm64").output();
        if let Ok(out) = sysctl {
            if String::from_utf8_lossy(&out.stdout).trim() == "1" {
                gpu = HardwareType::AppleSilicon;
            }
        }
    }

    #[cfg(target_os = "windows")]
    {
        gpu = HardwareType::Nvidia;
    }

    SystemProfile { os, arch, gpu }
}

fn get_linux_distro() -> String {
    if let Ok(content) = std::fs::read_to_string("/etc/os-release") {
        for line in content.lines() {
            if line.starts_with("ID=") {
                return line.trim_start_matches("ID=").trim_matches('"').to_string();
            }
        }
    }
    "unknown".to_string()
}

pub async fn run_provisioning() -> Result<()> {
    let profile = detect_profile();
    info!("Starting Autonomous Provisioning for {}/{}...", profile.os, profile.arch);

    let mut commands = Vec::new();

    if profile.os == "linux" {
        let distro = get_linux_distro();
        match distro.as_str() {
            "arch" | "cachyos" | "manjaro" => {
                match profile.gpu {
                    HardwareType::Nvidia => {
                        commands.push(
                            "sudo pacman -S --needed --noconfirm docker nvidia-container-toolkit",
                        );
                        commands.push("sudo nvidia-ctk runtime configure --runtime=docker");
                    }
                    HardwareType::Amd => {
                        commands
                            .push("sudo pacman -S --needed --noconfirm docker rocm-opencl-runtime");
                    }
                    _ => commands.push("sudo pacman -S --needed --noconfirm docker"),
                }
                commands.push("sudo systemctl enable --now docker");
            }
            "fedora" => {
                commands.push("sudo dnf install -y docker-ce docker-ce-cli containerd.io");
                if let HardwareType::Nvidia = profile.gpu {
                    commands.push("sudo dnf install -y nvidia-container-toolkit");
                    commands.push("sudo nvidia-ctk runtime configure --runtime=docker");
                }
                commands.push("sudo systemctl enable --now docker");
            }
            "ubuntu" | "debian" | "pop" | "mint" => {
                commands.push("sudo apt-get update");
                commands.push("sudo apt-get install -y docker.io");
                if let HardwareType::Nvidia = profile.gpu {
                    commands.push("sudo apt-get install -y nvidia-container-toolkit");
                    commands.push("sudo nvidia-ctk runtime configure --runtime=docker");
                }
                commands.push("sudo systemctl enable --now docker");
            }
            _ => {
                warn!("Unknown Linux distribution: {}. Falling back to generic advice.", distro);
                commands.push(
                    "curl -fsSL https://get.docker.com -o get-docker.sh && sudo sh get-docker.sh",
                );
            }
        }
        commands.push("sudo usermod -aG docker $USER");
    } else if profile.os == "macos" {
        println!("\n{} Neurex detected macOS ({}).", "🍎".bright_white(), profile.arch);
        println!("Opening Docker Desktop for Mac download page...");
        let _ = Command::new("open").arg("https://www.docker.com/products/docker-desktop").spawn();
    } else if profile.os == "windows" {
        println!("\n{} Neurex detected Windows.", "🪟".bright_blue());
        println!("Opening Docker Desktop for Windows download page...");
        let _ = Command::new("powershell")
            .arg("Start-Process")
            .arg("https://www.docker.com/products/docker-desktop")
            .spawn();
    }

    if commands.is_empty() {
        info!("Provisioning steps initiated (Browser links opened or environment ready).");
        return Ok(());
    }

    println!("\n{}", "🚀 Neurex is ready to provision your environment:".bold().green());
    for cmd in &commands {
        println!("   $ {}", cmd.cyan());
    }

    print!("\nDo you authorize Neurex to execute these commands? (y/N): ");
    io::stdout().flush()?;

    let mut input = String::new();
    io::stdin().read_line(&mut input)?;

    if input.trim().to_lowercase() == "y" {
        for cmd in commands {
            info!("Executing: {}", cmd);
            let status = Command::new("sh").arg("-c").arg(cmd).status()?;

            if !status.success() {
                error!("Command failed: {}", cmd);
                bail!("Provisioning failed during execution.");
            }
        }

        // Setup Storage Paths
        setup_storage_paths().await?;

        info!("Provisioning successful! Please log out and back in to apply group changes.");
    } else {
        warn!("Provisioning aborted by user.");
    }

    Ok(())
}

async fn setup_storage_paths() -> Result<()> {
    println!("\n{}", "📂 Neurex Storage Configuration".bold().purple());
    println!("Please configure your primary storage paths. Press Enter to use defaults.");

    let default_install = format!("{}/.neurex", dirs::home_dir().unwrap().to_string_lossy());
    let default_models = format!("{}/.ollama/models", dirs::home_dir().unwrap().to_string_lossy());
    let default_scan = dirs::home_dir().unwrap().to_string_lossy().to_string();

    print!("Installation Directory [{}]: ", default_install.cyan());
    io::stdout().flush()?;
    let mut install_dir = String::new();
    io::stdin().read_line(&mut install_dir)?;
    let install_dir = if install_dir.trim().is_empty() {
        default_install
    } else {
        install_dir.trim().to_string()
    };

    print!("Model Storage Directory [{}]: ", default_models.cyan());
    io::stdout().flush()?;
    let mut models_dir = String::new();
    io::stdin().read_line(&mut models_dir)?;
    let models_dir =
        if models_dir.trim().is_empty() { default_models } else { models_dir.trim().to_string() };

    print!("Telemetry Scan Paths (comma separated) [{}]: ", default_scan.cyan());
    io::stdout().flush()?;
    let mut scan_paths_raw = String::new();
    io::stdin().read_line(&mut scan_paths_raw)?;
    let scan_paths: Vec<String> = if scan_paths_raw.trim().is_empty() {
        vec![default_scan]
    } else {
        scan_paths_raw.split(',').map(|s| s.trim().to_string()).collect()
    };

    // Prepare settings JSON
    let mut settings = serde_json::json!({
        "neurex_install_dir": install_dir,
        "models_dir": models_dir,
        "storage_paths": scan_paths,
        "validate_path_permissions": true
    });

    // Merge with existing if present
    let settings_path = dirs::home_dir().unwrap().join(".neurex_settings.json");
    if settings_path.exists()
        && let Ok(content) = std::fs::read_to_string(&settings_path)
        && let Ok(mut existing) = serde_json::from_str::<serde_json::Value>(&content)
        && let Some(obj) = existing.as_object_mut()
    {
        obj.insert("neurex_install_dir".to_string(), serde_json::Value::String(install_dir));
        obj.insert("models_dir".to_string(), serde_json::Value::String(models_dir));
        obj.insert("storage_paths".to_string(), serde_json::to_value(scan_paths)?);
        settings = existing;
    }

    std::fs::write(&settings_path, serde_json::to_string_pretty(&settings)?)?;
    info!("Storage configuration saved to {}", settings_path.display());

    Ok(())
}
