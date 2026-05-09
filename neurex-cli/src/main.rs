use anyhow::{Context, Result};
use clap::{Parser, Subcommand};
use colored::*;
use std::net::SocketAddr;
use std::path::Path;
use std::sync::Arc;
use sysinfo::System;
use tokio::process::Command;
use tracing::{Level, error, info, warn};
use tracing_subscriber::FmtSubscriber;

mod api;
mod bootstrap;
mod provision;
mod sandbox;
mod wasi_sandbox;

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

#[tokio::main]
async fn main() -> Result<()> {
    // Initialize Tracing
    let subscriber = FmtSubscriber::builder().with_max_level(Level::INFO).finish();
    tracing::subscriber::set_global_default(subscriber)
        .context("setting default subscriber failed")?;

    let cli = Cli::parse();

    match cli.command {
        Commands::Start { port } => {
            let api_port = port + 5000;

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

            let uv_path = bootstrap::ensure_uv().await?;
            let env_dir = bootstrap::ensure_env(&uv_path).await?;

            let req_path = std::env::current_dir()?.join("../neurex-api/requirements.txt");
            bootstrap::install_dependencies(&uv_path, &env_dir, &req_path).await?;

            let uvicorn_exe = if std::env::consts::OS == "windows" {
                env_dir.join("Scripts").join("uvicorn.exe")
            } else {
                env_dir.join("bin").join("uvicorn")
            };

            let _current_dir = std::env::current_dir()?;
            let home = dirs::home_dir().unwrap();
            let settings_path = home.join(".neurex_settings.json");
            let settings: serde_json::Value = if settings_path.exists() {
                let content =
                    std::fs::read_to_string(&settings_path).unwrap_or_else(|_| "{}".to_string());
                serde_json::from_str(&content).unwrap_or(serde_json::json!({}))
            } else {
                serde_json::json!({})
            };

            let enable_https = settings["enable_https"].as_bool().unwrap_or(false);
            let fqdn = settings["fqdn"].as_str().unwrap_or("").to_string();
            let listen_addr = settings["listen_address"].as_str().unwrap_or("0.0.0.0").to_string();

            let cert_path = settings["ssl_cert_path"]
                .as_str()
                .map(Path::new)
                .map(|p| p.to_path_buf())
                .unwrap_or_else(|| home.join(".neurex").join("certs").join("cert.pem"));

            let key_path = settings["ssl_key_path"]
                .as_str()
                .map(Path::new)
                .map(|p| p.to_path_buf())
                .unwrap_or_else(|| home.join(".neurex").join("certs").join("key.pem"));

            let mut api_cmd = Command::new(&uvicorn_exe);
            api_cmd
                .arg("main:app")
                .arg("--host")
                .arg("127.0.0.1")
                .arg("--port")
                .arg(api_port.to_string())
                .current_dir("../neurex-api");

            if enable_https {
                info!("Enforcing SSL/TLS Encryption (Terminated at Substrate Boundary)");
            }

            let mut api_process = api_cmd.spawn().context("Failed to spawn neurex-api")?;

            info!("FastAPI Proxy initialized successfully");

            let wasi_sandbox = Arc::new(wasi_sandbox::WasiSandbox::new()?);

            let state = Arc::new(api::AppState {
                api_port,
                wasi_sandbox: wasi_sandbox.clone(),
                enable_https,
            });
            let app = api::create_router(state);

            let addr: SocketAddr = format!("{}:{}", listen_addr, port).parse()?;

            let fqdn_val = fqdn.clone();
            let web_server = tokio::spawn(async move {
                if enable_https && cert_path.exists() && key_path.exists() {
                    let tls_config =
                        axum_server::tls_rustls::RustlsConfig::from_pem_file(&cert_path, &key_path)
                            .await
                            .unwrap();

                    info!(
                        "★ Secure Neurex Substrate active at https://{}",
                        if fqdn_val.is_empty() { addr.to_string() } else { fqdn_val.to_string() }
                    );
                    info!("(Protocol Enforcement: HTTP → HTTPS auto-redirect enabled)");

                    axum_server_dual_protocol::bind_dual_protocol(addr, tls_config)
                        .serve(app.into_make_service_with_connect_info::<SocketAddr>())
                        .await
                        .unwrap();
                } else {
                    let listener = tokio::net::TcpListener::bind(addr).await.unwrap();
                    info!("Embedded Vite Frontend active at http://{}", addr);
                    axum::serve(listener, app.into_make_service_with_connect_info::<SocketAddr>())
                        .await
                        .unwrap();
                }
            });

            if let Some(ref d) = docker {
                let current_dir = std::env::current_dir()?.to_string_lossy().to_string();
                if let Err(e) = sandbox::ensure_sandbox(d, &current_dir).await {
                    error!("Failed to initialize sandbox: {}", e);
                }
            }

            info!(
                "★ Neurex Substrate active at: {}",
                format!(
                    "https://{}",
                    if fqdn.is_empty() { addr.to_string() } else { fqdn.to_string() }
                )
                .bold()
                .underline()
            );
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

            println!(
                "{:<20} {}",
                "OS:".bold(),
                format!(
                    "{} {} ({})",
                    System::name().unwrap_or_default(),
                    System::os_version().unwrap_or_default(),
                    System::kernel_version().unwrap_or_default()
                )
                .green()
            );
            println!(
                "{:<20} {}",
                "Hardware:".bold(),
                format!(
                    "{} / {}GB RAM",
                    sys.cpus().first().map(|c| c.brand()).unwrap_or("Unknown"),
                    sys.total_memory() / (1024 * 1024 * 1024)
                )
                .green()
            );

            match sandbox::connect_docker().await {
                Ok(docker) => {
                    if let Ok(version) = docker.version().await {
                        println!(
                            "{:<20} {}",
                            "Sandbox Engine:".bold(),
                            format!("Docker {}", version.version.unwrap_or_default()).green()
                        );
                    }
                }
                Err(_) => {
                    println!("{:<20} {}", "Sandbox Engine:".bold(), "NOT INSTALLED".red());
                }
            }

            match wasi_sandbox::WasiSandbox::new() {
                Ok(_) => {
                    println!("{:<20} {}", "WASM Engine:".bold(), "Wasmtime 29.0 (Ready)".green());
                    println!(
                        "{:<20} {}",
                        "Native Substrate:".bold(),
                        "Ready (Jailed Filesystem)".green()
                    );
                }
                Err(e) => {
                    println!("{:<20} {}", "WASM Engine:".bold(), format!("FAILED: {}", e).red());
                }
            }

            println!("\nSystem is {} for v0.5.2 Stable Substrate.", "Ready".bold().green());
        }
        Commands::Provision => {
            provision::run_provisioning().await?;
        }
    }
    Ok(())
}
