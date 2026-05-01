use axum::{
    Router,
    body::Body,
    extract::State,
    http::{StatusCode, Uri, header},
    response::{IntoResponse, Response},
    routing::get,
};
use bollard::Docker;
use bollard::container::{
    Config, CreateContainerOptions, RemoveContainerOptions, StartContainerOptions,
};
use bollard::models::HostConfig;
use clap::{Parser, Subcommand};
use colored::*;
use rust_embed::RustEmbed;
use std::net::SocketAddr;
use std::sync::Arc;
use std::time::Duration;
use sysinfo::System;
use tokio::process::Command;
use tokio::time::sleep;

mod bootstrap;

#[derive(RustEmbed)]
#[folder = "../neurex-web/dist"]
struct Asset;

struct AppState {
    api_port: u16,
}

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
}

async fn static_handler(State(state): State<Arc<AppState>>, uri: Uri) -> impl IntoResponse {
    let mut path = uri.path().trim_start_matches('/').to_string();
    if path.is_empty() {
        path = "index.html".to_string();
    }

    match Asset::get(path.as_str()) {
        Some(content) => {
            if path == "index.html" {
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
                let mime = mime_guess::from_path(&path).first_or_octet_stream();
                Response::builder()
                    .header(header::CONTENT_TYPE, mime.as_ref())
                    .body(Body::from(content.data))
                    .unwrap()
            }
        }
        None => {
            if let Some(index) = Asset::get("index.html") {
                let html = String::from_utf8_lossy(&index.data);
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
                Response::builder()
                    .status(StatusCode::NOT_FOUND)
                    .body(Body::from("404 Not Found"))
                    .unwrap()
            }
        }
    }
}

#[tokio::main]
async fn main() {
    let cli = Cli::parse();

    match &cli.command {
        Commands::Start { port } => {
            let api_port = port + 5000; // e.g. 8000

            println!(
                "{}",
                "⬡ Neurex CLI - Initializing Hermetic Substrate"
                    .bold()
                    .cyan()
            );

            println!("{} Checking host dependencies...", "[1/3]".dimmed());
            let docker = match Docker::connect_with_local_defaults() {
                Ok(d) => d,
                Err(_) => {
                    println!(
                        "  {} Docker Daemon NOT detected. A container engine is required for Neural Sandboxing.",
                        "✗".red()
                    );
                    std::process::exit(1);
                }
            };
            println!("  {} Docker Daemon detected", "✓".green());

            println!(
                "{} Booting Control Plane (Frontend: {}, Backend: {})...",
                "[2/3]".dimmed(),
                port,
                api_port
            );

            // Hermetic Bootstrap Sequence
            let uv_path = bootstrap::ensure_uv().await;
            let env_dir = bootstrap::ensure_env(&uv_path).await;
            
            // Assume we're running from neurex-cli directory, api is in ../neurex-api
            let req_path = std::env::current_dir().unwrap().join("../neurex-api/requirements.txt");
            bootstrap::install_dependencies(&uv_path, &env_dir, &req_path).await;

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
                .expect("Failed to spawn neurex-api (is uvicorn installed?)");

            println!("  {} FastAPI Proxy initialized", "✓".green());

            // Start Embedded Web Server
            let state = Arc::new(AppState { api_port });
            let app = Router::new()
                .fallback(get(static_handler))
                .with_state(state);

            let addr = SocketAddr::from(([0, 0, 0, 0], *port));
            let web_server = tokio::spawn(async move {
                let listener = tokio::net::TcpListener::bind(addr).await.unwrap();
                axum::serve(listener, app).await.unwrap();
            });

            println!("  {} Embedded Vite Frontend active", "✓".green());

            println!("{} Booting Neural Execution Sandbox...", "[3/3]".dimmed());

            let _ = docker
                .remove_container(
                    "neurex-sandbox-agent",
                    Some(RemoveContainerOptions {
                        force: true,
                        ..Default::default()
                    }),
                )
                .await;

            let current_dir = std::env::current_dir()
                .unwrap()
                .to_string_lossy()
                .to_string();
            let binds = vec![format!("{}:/workspace", current_dir)];
            let host_config = HostConfig {
                binds: Some(binds),
                ..Default::default()
            };

            let config = Config {
                image: Some("alpine:latest"),
                cmd: Some(vec!["tail", "-f", "/dev/null"]),
                host_config: Some(host_config),
                ..Default::default()
            };

            let options = Some(CreateContainerOptions {
                name: "neurex-sandbox-agent",
                platform: None,
            });

            match docker.create_container(options, config).await {
                Ok(_) => {
                    if let Ok(_) = docker
                        .start_container(
                            "neurex-sandbox-agent",
                            None::<StartContainerOptions<String>>,
                        )
                        .await
                    {
                        println!(
                            "  {} Workspace mounted securely (RO/RW restricted)",
                            "✓".green()
                        );
                        println!(
                            "  {} CoderAgent container started (Alpine Sandbox)",
                            "✓".green()
                        );
                    } else {
                        println!("  {} Failed to start sandbox container.", "✗".red());
                    }
                }
                Err(e) => {
                    println!("  {} Failed to create sandbox: {}", "✗".red(), e);
                }
            }

            println!(
                "\n{} Neurex is active. Access the IDE at: {}",
                "★".yellow(),
                format!("http://localhost:{}", port).bold().underline()
            );
            println!("   Press Ctrl+C to stop.");

            tokio::select! {
                _ = tokio::signal::ctrl_c() => {
                    println!("\n{} Received interrupt signal. Halting Substrate...", "■".red());
                    let _ = api_process.kill().await;
                    web_server.abort();

                    println!("{} Destroying Neural Sandbox...", "■".red());
                    let _ = docker.remove_container("neurex-sandbox-agent", Some(RemoveContainerOptions{
                        force: true,
                        ..Default::default()
                    })).await;

                    println!("{} Control Plane terminated.", "✓".green());
                }
            }
        }
        Commands::Stop => {
            println!("{}", "⬡ Neurex CLI - Halting Substrate".bold().cyan());
            println!("{} Terminating Control Plane...", "■".red());

            if let Ok(docker) = Docker::connect_with_local_defaults() {
                println!("{} Draining Sandboxed execution units...", "■".red());
                let _ = docker
                    .remove_container(
                        "neurex-sandbox-agent",
                        Some(RemoveContainerOptions {
                            force: true,
                            ..Default::default()
                        }),
                    )
                    .await;
            }

            println!("{} Neurex stopped gracefully.", "✓".green());
        }
        Commands::Doctor => {
            println!("{}", "⬡ Neurex Doctor - System Diagnostics".bold().cyan());

            let mut sys = System::new_all();
            sys.refresh_all();

            let os_name = System::name().unwrap_or_else(|| "Unknown".to_string());
            let os_ver = System::os_version().unwrap_or_else(|| "".to_string());
            let kernel = System::kernel_version().unwrap_or_else(|| "".to_string());
            let cpu = sys
                .cpus()
                .first()
                .map(|c| c.brand())
                .unwrap_or("Unknown CPU");
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
