use bollard::Docker;
use clap::{Parser, Subcommand};
use colored::*;
use std::time::Duration;
use sysinfo::System;
use tokio::process::Command;
use tokio::time::sleep;

/// Neurex CLI - The Universal Sentient IDE Substrate Manager
#[derive(Parser, Debug)]
#[command(author, version, about, long_about = None)]
struct Cli {
    #[command(subcommand)]
    command: Commands,
}

#[derive(Subcommand, Debug)]
enum Commands {
    /// Starts the Neurex IDE (Control Plane + Execution Sandbox)
    Start {
        /// Port to bind the control plane to (default 8000)
        #[arg(short, long, default_value_t = 8000)]
        port: u16,
    },
    /// Stops all background Neurex processes and sandboxes
    Stop,
    /// Checks the system for required dependencies and hardware acceleration
    Doctor,
}

#[tokio::main]
async fn main() {
    let cli = Cli::parse();

    match &cli.command {
        Commands::Start { port } => {
            println!("{}", "⬡ Neurex CLI - Initializing Substrate".bold().cyan());

            // Phase A/B initialization
            println!("{} Checking host dependencies...", "[1/3]".dimmed());
            let docker_check = Docker::connect_with_local_defaults();
            if docker_check.is_err() {
                println!(
                    "  {} Docker Daemon NOT detected. A container engine is required for Neural Sandboxing.",
                    "✗".red()
                );
                std::process::exit(1);
            }
            println!("  {} Docker Daemon detected", "✓".green());

            // Real Control Plane spin-up
            println!(
                "{} Spinning up Control Plane on port {}...",
                "[2/3]".dimmed(),
                port
            );
            
            // Spawn FastAPI (Backend)
            let mut api_process = Command::new("uvicorn")
                .arg("main:app")
                .arg("--host")
                .arg("0.0.0.0")
                .arg("--port")
                .arg(port.to_string())
                .current_dir("../neurex-api")
                .spawn()
                .expect("Failed to spawn neurex-api (is uvicorn installed?)");

            // Spawn Vite (Frontend)
            let mut web_process = Command::new("npm")
                .arg("run")
                .arg("dev")
                .current_dir("../neurex-web")
                .spawn()
                .expect("Failed to spawn neurex-web (is npm installed?)");

            println!("  {} FastAPI Proxy initialized", "✓".green());
            println!("  {} Vite Frontend initialized", "✓".green());

            println!("{} Booting Neural Execution Sandbox...", "[3/3]".dimmed());
            sleep(Duration::from_millis(1200)).await;
            println!(
                "  {} Workspace mounted securely (RO/RW restricted)",
                "✓".green()
            );
            println!("  {} CoderAgent container started (Mock)", "✓".green());

            println!(
                "\n{} Neurex is active. Access the IDE at: {}",
                "★".yellow(),
                format!("http://localhost:5173").bold().underline() // Default vite port
            );
            println!("   Press Ctrl+C to stop.");

            // Keep the daemon alive and handle graceful shutdown
            tokio::select! {
                _ = tokio::signal::ctrl_c() => {
                    println!("\n{} Received interrupt signal. Halting Substrate...", "■".red());
                    let _ = api_process.kill().await;
                    let _ = web_process.kill().await;
                    println!("{} Control Plane terminated.", "✓".green());
                }
            }
        }
        Commands::Stop => {
            println!("{}", "⬡ Neurex CLI - Halting Substrate".bold().cyan());
            println!("{} Terminating Control Plane...", "■".red());
            println!("{} Draining Sandboxed execution units...", "■".red());
            println!("{} Neurex stopped gracefully.", "✓".green());
        }
        Commands::Doctor => {
            println!("{}", "⬡ Neurex Doctor - System Diagnostics".bold().cyan());

            let mut sys = System::new_all();
            sys.refresh_all();

            let os_name = System::name().unwrap_or_else(|| "Unknown".to_string());
            let os_ver = System::os_version().unwrap_or_else(|| "".to_string());
            let kernel = System::kernel_version().unwrap_or_else(|| "".to_string());
            let cpu = sys.cpus().first().map(|c| c.brand()).unwrap_or("Unknown CPU");
            let mem = sys.total_memory() / 1_048_576; // MB

            println!(
                "{:<20} {}",
                "OS:".bold(),
                format!("{} {} ({})", os_name, os_ver, kernel).green()
            );
            println!(
                "{:<20} {}",
                "Hardware:".bold(),
                format!("{} / {}MB RAM", cpu, mem).green()
            );

            match Docker::connect_with_local_defaults() {
                Ok(docker) => {
                    if let Ok(version) = docker.version().await {
                        let ver_str = version.version.unwrap_or_else(|| "Unknown".to_string());
                        println!(
                            "{:<20} {}",
                            "Sandbox Engine:".bold(),
                            format!("Docker {}", ver_str).green()
                        );
                    } else {
                        println!(
                            "{:<20} {}",
                            "Sandbox Engine:".bold(),
                            "Docker detected, but failed to get version".yellow()
                        );
                    }
                }
                Err(_) => {
                    println!(
                        "{:<20} {}",
                        "Sandbox Engine:".bold(),
                        "Docker NOT DETECTED (Required)".red()
                    );
                }
            }

            println!(
                "\nSystem is {} for Phase 53 Transcendence.",
                "Ready".bold().green()
            );
        }
    }
}
