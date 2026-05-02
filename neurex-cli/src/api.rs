use anyhow::Result;
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

pub async fn sandbox_exec_handler(
    State(state): State<Arc<AppState>>,
    axum::Json(payload): axum::Json<SandboxExecRequest>,
) -> impl IntoResponse {
    let current_dir = std::env::current_dir().unwrap();

    // 1. WASM Execution Path
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
        // 2. Native Fallback Path
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

    let serve_asset = |p: &str| -> Option<Response<Body>> {
        match Asset::get(p) {
            Some(content) => {
                let mime = mime_guess::from_path(p).first_or_octet_stream();
                let body = Body::from(content.data.into_owned());
                
                // Inject runtime API variables if serving index.html
                if p == "index.html" {
                    let html = String::from_utf8_lossy(&content.data);
                    let injected = html.replace(
                        "window.__NEUREX_CONFIG__ = {}",
                        &format!("window.__NEUREX_CONFIG__ = {{ apiPort: {} }}", state.api_port)
                    );
                    let body = Body::from(injected);
                    return Some(Response::builder()
                        .header(header::CONTENT_TYPE, "text/html")
                        .body(body)
                        .unwrap());
                }

                Some(Response::builder()
                    .header(header::CONTENT_TYPE, mime.as_ref())
                    .body(body)
                    .unwrap())
            }
            None => None,
        }
    };

    match serve_asset(&path) {
        Some(response) => response,
        None => (StatusCode::NOT_FOUND, Body::from("Not Found")).into_response(),
    }
}

pub fn create_router(state: Arc<AppState>) -> Router {
    Router::new()
        .route("/api/sandbox/exec", post(sandbox_exec_handler))
        .fallback(get(static_handler))
        .with_state(state)
}
