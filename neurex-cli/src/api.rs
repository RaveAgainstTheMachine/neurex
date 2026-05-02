// use anyhow::Result;
use axum::{
    Router,
    body::Body,
    extract::State,
    http::{StatusCode, Uri, header},
    response::{IntoResponse, Response},
    routing::{get, post},
};
use rust_embed::RustEmbed;
use std::sync::Arc;
use std::path::Path;
use tracing::{info, error};
use serde::{Deserialize, Serialize};

use crate::wasi_sandbox;
use crate::sandbox;

#[derive(RustEmbed)]
#[folder = "../neurex-web/dist"]
pub struct Asset;

pub struct AppState {
    pub api_port: u16,
    pub wasi_sandbox: Arc<wasi_sandbox::WasiSandbox>,
}

#[derive(Deserialize)]
pub struct SandboxExecRequest {
    pub wasm_path: Option<String>,
    pub args: Vec<String>,
}

#[derive(Serialize)]
pub struct SandboxExecResponse {
    pub stdout: String,
    pub stderr: String,
    pub exit_code: i32,
    pub error: Option<String>,
}

#[derive(Serialize)]
pub struct SubstrateStatus {
    pub docker: DockerStatus,
    pub wasm: WasmStatus,
    pub hardware: HardwareStatus,
}

#[derive(Serialize)]
pub struct DockerStatus {
    pub active: bool,
    pub version: Option<String>,
    pub gpu_acceleration: bool,
}

#[derive(Serialize)]
pub struct WasmStatus {
    pub active: bool,
    pub coreutils_present: bool,
}

#[derive(Serialize)]
pub struct HardwareStatus {
    pub os: String,
    pub arch: String,
    pub cpu: String,
    pub ram_gb: u64,
}

pub async fn substrate_status_handler(
    State(_state): State<Arc<AppState>>,
) -> impl IntoResponse {
    use sysinfo::System;
    let mut sys = System::new_all();
    sys.refresh_all();

    let docker_info = match sandbox::connect_docker().await {
        Ok(d) => {
            let ver = d.version().await.ok().and_then(|v| v.version);
            let has_nvidia = std::path::Path::new("/dev/nvidia0").exists();
            DockerStatus { active: true, version: ver, gpu_acceleration: has_nvidia }
        }
        Err(_) => DockerStatus { active: false, version: None, gpu_acceleration: false }
    };

    let home = std::env::var("HOME").unwrap_or_else(|_| ".".to_string());
    let wasm_path = Path::new(&home).join(".neurex").join("bin").join("coreutils.wasm");
    let wasm_info = WasmStatus {
        active: true, // Wasmtime is embedded
        coreutils_present: wasm_path.exists(),
    };

    let hw_info = HardwareStatus {
        os: std::env::consts::OS.to_string(),
        arch: std::env::consts::ARCH.to_string(),
        cpu: sys.cpus().first().map(|c| c.brand()).unwrap_or("Unknown").to_string(),
        ram_gb: sys.total_memory() / (1024 * 1024 * 1024), // Convert to GB
    };

    axum::Json(SubstrateStatus {
        docker: docker_info,
        wasm: wasm_info,
        hardware: hw_info,
    })
}

pub async fn sandbox_exec_handler(
    State(state): State<Arc<AppState>>,
    axum::Json(payload): axum::Json<SandboxExecRequest>,
) -> impl IntoResponse {
    let current_dir = std::env::current_dir().unwrap();

    if let Some(path) = payload.wasm_path {
        let wasm_path = Path::new(&path);
        if !wasm_path.exists() {
            return (StatusCode::NOT_FOUND, axum::Json(SandboxExecResponse {
                stdout: "".into(),
                stderr: "".into(),
                exit_code: -1,
                error: Some("WASM module not found".into()),
            }));
        }

        let wasm_bytes = match std::fs::read(wasm_path) {
            Ok(b) => b,
            Err(e) => return (StatusCode::INTERNAL_SERVER_ERROR, axum::Json(SandboxExecResponse {
                stdout: "".into(),
                stderr: "".into(),
                exit_code: -1,
                error: Some(format!("Failed to read WASM module: {}", e)),
            })),
        };

        match state.wasi_sandbox.run_module(&wasm_bytes, &current_dir, payload.args) {
            Ok(res) => (StatusCode::OK, axum::Json(SandboxExecResponse {
                stdout: res.stdout,
                stderr: res.stderr,
                exit_code: res.exit_code,
                error: None,
            })),
            Err(e) => (StatusCode::INTERNAL_SERVER_ERROR, axum::Json(SandboxExecResponse {
                stdout: "".into(),
                stderr: "".into(),
                exit_code: -1,
                error: Some(format!("WASM Execution failed: {}", e)),
            })),
        }
    } else {
        let executor = sandbox::NativeExecutor::new(&current_dir.to_string_lossy());
        let command = payload.args.join(" "); 
        match executor.execute(&command) {
            Ok(res) => (StatusCode::OK, axum::Json(SandboxExecResponse {
                stdout: res.stdout,
                stderr: res.stderr,
                exit_code: res.exit_code,
                error: None,
            })),
            Err(e) => (StatusCode::INTERNAL_SERVER_ERROR, axum::Json(SandboxExecResponse {
                stdout: "".into(),
                stderr: "".into(),
                exit_code: -1,
                error: Some(format!("Native Execution failed: {}", e)),
            })),
        }
    }
}

pub async fn static_handler(State(state): State<Arc<AppState>>, uri: Uri) -> impl IntoResponse {
    let mut path = uri.path().trim_start_matches('/').to_string();
    if path.is_empty() {
        path = "index.html".to_string();
    }

    match Asset::get(&path) {
        Some(content) => {
            let mime = mime_guess::from_path(&path).first_or_octet_stream();
            
            if path == "index.html" {
                let html = String::from_utf8_lossy(&content.data);
                let injected = html.replace(
                    "window.__NEUREX_CONFIG__ = {}",
                    &format!("window.__NEUREX_CONFIG__ = {{ apiPort: {} }}", state.api_port)
                );
                return Response::builder()
                    .header(header::CONTENT_TYPE, "text/html")
                    .body(Body::from(injected))
                    .unwrap()
                    .into_response();
            }

            Response::builder()
                .header(header::CONTENT_TYPE, mime.as_ref())
                .body(Body::from(content.data.to_vec()))
                .unwrap()
                .into_response()
        }
        None => (StatusCode::NOT_FOUND, Body::from("Not Found")).into_response(),
    }
}

pub async fn proxy_handler(
    State(state): State<Arc<AppState>>,
    method: axum::http::Method,
    uri: Uri,
    body: Body,
) -> impl IntoResponse {
    let api_url = format!("http://127.0.0.1:{}{}", state.api_port, uri.path());
    let client = reqwest::Client::new();
    
    // Convert Axum body to bytes to send via reqwest
    let body_bytes = match axum::body::to_bytes(body, 10 * 1024 * 1024).await {
        Ok(b) => b,
        Err(e) => return (StatusCode::BAD_REQUEST, format!("Body too large: {}", e)).into_response(),
    };

    let resp = client.request(method, &api_url)
        .body(body_bytes)
        .send()
        .await;
    
    match resp {
        Ok(r) => {
            let status = r.status();
            let bytes = r.bytes().await.unwrap_or_default();
            Response::builder()
                .status(StatusCode::from_u16(status.as_u16()).unwrap())
                .header(header::CONTENT_TYPE, "application/json")
                .body(Body::from(bytes))
                .unwrap()
                .into_response()
        }
        Err(e) => {
            error!("Proxy Error: {}", e);
            (StatusCode::BAD_GATEWAY, "Gateway Error").into_response()
        }
    }
}

use axum::routing::any;

pub fn create_router(state: Arc<AppState>) -> Router {
    Router::new()
        .route("/api/sandbox/exec", post(sandbox_exec_handler))
        .route("/api/substrate/status", get(substrate_status_handler))
        .route("/api/{*path}", any(proxy_handler))
        .fallback(get(static_handler))
        .with_state(state)
}
