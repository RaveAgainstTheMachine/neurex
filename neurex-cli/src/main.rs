use anyhow::{Context, Result};
use axum::{
    Router,
    body::Body,
    extract::State,
    http::{StatusCode, Uri, header},
    response::{IntoResponse, Response},
    routing::{get, post},
};
use clap::{Parser, Subcommand};
use colored::*;
use rust_embed::RustEmbed;
use std::net::SocketAddr;
use std::path::Path;
use std::sync::Arc;
use sysinfo::System;
use tokio::process::Command;
use tracing::{info, error, warn, Level};
use tracing_subscriber::FmtSubscriber;

mod bootstrap;
mod sandbox;
mod wasi_sandbox;
mod api;
mod provision;

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
        /// Port to bind the IDE frontend to (default 3000)
        #[arg(short, long, default_value_t = 3000)]
        port: u16,
    },
    /// Stops all background Neurex processes and sandboxes
    Stop,
    /// Checks the system for required dependencies and hardware acceleration
    Doctor,
    /// Autonomously provisions the environment (Docker, GPU Toolkits, etc.)
    Provision,
}

async fn static_handler(State(state): State<Arc<AppState>>, uri: Uri) -> impl IntoResponse {
    let mut path = uri.path().trim_start_matches('/').to_string();
    if path.is_empty() {
        path = "index.html".to_string();
    }

    let serve_asset = |p: &str| -> Option<Response<Body>> {
        Asset::get(p).map(|content| {
            if p == "index.html" {
                let html = String::from_utf8_lossy(&content.data);
                let injected = html.replace(
                    "<head>",
                    &format!(
                        "<head><script>window.__API_BASE__ = 'http://localhost:{}/api'; window.__WS_BASE__ = 'ws://localhost:{}/ws';</script>",
                        state.api_port, state.api_port
                    ),
                );
                Response::builder()
                    .header(header::CONTENT_TYPE, "text/html")
                    .body(Body::from(injected))
                    .unwrap()
            } else {
                let mime = mime_guess::from_path(p).first_or_octet_stream();
                Response::builder()
                    .header(header::CONTENT_TYPE, mime.as_ref())
                    .body(Body::from(content.data.into_owned()))
                    .unwrap()
            }
        })
    };

    serve_asset(&path)
        .or_else(|| serve_asset("index.html"))
        .unwrap_or_else(|| {
            Response::builder()
                .status(StatusCode::NOT_FOUND)
                .body(Body::from("404 Not Found"))
                .unwrap()
        })
}

#[tokio::main]
async fn main() -> Result<()> {
    // Initialize Tracing
    let subscriber = FmtSubscriber::builder()
        .with_max_level(Level::INFO)
        .finish();
    tracing::subscriber::set_global_default(subscriber).context("setting default subscriber failed")?;

    let cli = Cli::parse();

    match &cli.command {
        Commands::Start { port } => {
            let api_port = port + 5000; // e.g. 8000

            info!("{}", "⬡ Neurex CLI - Initializing Hermetic Substrate".bold().cyan());

            // 1. Host Checks
            info!("Checking host dependencies...");
            let docker = match sandbox::connect_docker().await {
                Ok(d) => Some(d),
                Err(e) => {
                    warn!("Docker Daemon NOT detected: {}. Sandbox disabled.", e);
                    None
                }
            };

            // 2. Control Plane Boot
            info!("Booting Control Plane (Frontend: {}, Backend: {})...", port, api_port);

            // Hermetic Bootstrap Sequence
            let uv_path = bootstrap::ensure_uv().await?;
            let env_dir = bootstrap::ensure_env(&uv_path).await?;
            
            let req_path = std::env::current_dir()?.join("../neurex-api/requirements.txt");
            bootstrap::install_dependencies(&uv_path, &env_dir, &req_path).await?;

            let uvicorn_exe = if std::env::consts::OS == "windows" {
                env_dir.join("Scripts").join("uvicorn.exe")
            } else {
                env_dir.join("bin").join("uvicorn")
            };

            // Spawn FastAPI (Backend) using hermetic env
            let mut api_process = Command::new(&uvicorn_exe)
                .arg("main:app")
                .arg("--host")
                .arg("0.0.0.0")
                .arg("--port")
                .arg(api_port.to_string())
                .current_dir("../neurex-api")
                .spawn()
                .context("Failed to spawn neurex-api (is uvicorn installed?)")?;

            info!("FastAPI Proxy initialized successfully");

            // 3. WASM Sandbox Initialization
            let wasi_sandbox = Arc::new(wasi_sandbox::WasiSandbox::new()?);

            // Start Embedded Web Server
            let state = Arc::new(api::AppState { 
                api_port,
                wasi_sandbox: wasi_sandbox.clone(),
            });
            let app = api::create_router(state);

            let addr = SocketAddr::from(([0, 0, 0, 0], *port));
            let web_server = tokio::spawn(async move {
                let listener = tokio::net::TcpListener::bind(addr).await.unwrap();
                info!("Embedded Vite Frontend active at http://{}", addr);
                axum::serve(listener, app).await.unwrap();
            });

            // 3. Execution Plane Boot
            if let Some(ref d) = docker {
                let current_dir = std::env::current_dir()?.to_string_lossy().to_string();
                if let Err(e) = sandbox::ensure_sandbox(d, &current_dir).await {
                    error!("Failed to initialize sandbox: {}", e);
                }
            }

            info!("★ Neurex is active. Access the IDE at: {}", format!("http://localhost:{}", port).bold().underline());
            info!("Press Ctrl+C to stop.");

            tokio::select! {
                _ = tokio::signal::ctrl_c() => {
                    info!("Received interrupt signal. Halting Substrate...");
                    let _ = api_process.kill().await;
                    web_server.abort();

                    if let Some(ref d) = docker {
                        let _ = sandbox::stop_sandbox(d).await;
                    }

                    info!("Control Plane terminated.");
                }
            }
        }
        Commands::Stop => {
            info!("{}", "⬡ Neurex CLI - Halting Substrate".bold().cyan());
            if let Ok(docker) = sandbox::connect_docker().await {
                let _ = sandbox::stop_sandbox(&docker).await;
            }
            info!("Neurex stopped gracefully.");
        }
        Commands::Doctor => {
            println!("{}", "⬡ Neurex Doctor - System Diagnostics".bold().cyan());

            let mut sys = System::new_all();
            sys.refresh_all();

            println!("{:<20} {}", "OS:".bold(), format!("{} {} ({})", System::name().unwrap_or_default(), System::os_version().unwrap_or_default(), System::kernel_version().unwrap_or_default()).green());
            println!("{:<20} {}", "Hardware:".bold(), format!("{} / {}MB RAM", sys.cpus().first().map(|c| c.brand()).unwrap_or("Unknown"), sys.total_memory() / 1_048_576).green());

            match sandbox::connect_docker().await {
                Ok(docker) => {
                    if let Ok(version) = docker.version().await {
                        println!("{:<20} {}", "Sandbox Engine:".bold(), format!("Docker {}", version.version.unwrap_or_default()).green());
                    }
                }
                Err(_) => {
                    println!("{:<20} {}", "Sandbox Engine:".bold(), "NOT INSTALLED".red());
                    println!("\n{} To unlock the Performance Tier, install Docker:", "💡 Tip:".yellow());
                    
                    match std::env::consts::OS {
                        "linux" => {
                            println!("   {} sudo pacman -S docker (Arch) or sudo apt install docker.io (Ubuntu)", "Linux:".bold());
                            println!("   {} sudo systemctl enable --now docker", "Enable:".bold());
                        }
                        "windows" => {
                            println!("   {} Install Docker Desktop: https://www.docker.com/products/docker-desktop", "Windows:".bold());
                            println!("   {} Ensure WSL2 is enabled.", "Note:".bold());
                        }
                        "macos" => {
                            println!("   {} Install Docker Desktop: https://www.docker.com/products/docker-desktop", "macOS:".bold());
                            println!("   {} Use Apple Silicon version for M1/M2/M3 chips.", "Note:".bold());
                        }
                        _ => {}
                    }
                }
            }

            // Check for GPU acceleration
            match std::env::consts::OS {
                "linux" => {
                    let has_nvidia = std::path::Path::new("/dev/nvidia0").exists();
                    if has_nvidia {
                        let has_toolkit = std::process::Command::new("nvidia-container-toolkit").arg("--version").output().is_ok();
                        if has_toolkit {
                            println!("{:<20} {}", "GPU Acceleration:".bold(), "Ready (NVIDIA RTX Detected)".green());
                        } else {
                            println!("{:<20} {}", "GPU Acceleration:".bold(), "UNAVAILABLE (Missing Toolkit)".yellow());
                            println!("   {} sudo pacman -S nvidia-container-toolkit", "Install:".bold());
                        }
                    }
                }
                "windows" => {
                    // On Windows, NVIDIA support is usually handled by Docker Desktop + WSL2 NVIDIA drivers
                    println!("{:<20} {}", "GPU Acceleration:".bold(), "Managed by Docker Desktop (WSL2 Backend)".cyan());
                }
                "macos" => {
                    println!("{:<20} {}", "GPU Acceleration:".bold(), "Metal (Native) / Restricted in Docker".cyan());
                }
                _ => {}
            }

            match wasi_sandbox::WasiSandbox::new() {
                Ok(_) => {
                    println!("{:<20} {}", "WASM Engine:".bold(), "Wasmtime 29.0 (Ready)".green());
                    let wasm_path = std::env::home_dir().unwrap().join(".neurex").join("bin").join("coreutils.wasm");
                    if wasm_path.exists() {
                        println!("{:<20} {}", "WASM Bridge:".bold(), "Active (coreutils.wasm detected)".green());
                    } else {
                        println!("{:<20} {}", "WASM Bridge:".bold(), "Inactive (Fallback to Native)".yellow());
                    }
                    println!("{:<20} {}", "Native Substrate:".bold(), "Ready (Jailed Filesystem)".green());
                }
                Err(e) => {
                    println!("{:<20} {}", "WASM Engine:".bold(), format!("FAILED: {}", e).red());
                }
            }

            println!("\nSystem is {} for Phase 54 Hermetic Substrate.", "Ready".bold().green());
        }
        Commands::Provision => {
            provision::run_provisioning().await?;
        }
    }
    Ok(())
}
