use std::net::SocketAddr;
use std::sync::Arc;
use axum::routing::get;
use axum::Router;
use reqwest::StatusCode;

use neurex_cli::api::{create_router, AppState};
use neurex_cli::wasi_sandbox::WasiSandbox;

#[tokio::test]
async fn test_server_startup_and_status_routing() {
    let wasi_sandbox = Arc::new(WasiSandbox::new().unwrap());
    let state = Arc::new(AppState {
        api_port: 8080,
        wasi_sandbox,
        enable_https: false,
    });

    let app = create_router(state);
    let listener = tokio::net::TcpListener::bind("127.0.0.1:0").await.unwrap();
    let addr = listener.local_addr().unwrap();

    let server_task = tokio::spawn(async move {
        axum::serve(listener, app.into_make_service_with_connect_info::<SocketAddr>())
            .await
            .unwrap();
    });

    // Verify substrate status endpoint is active and returns valid JSON matching our schema
    let client = reqwest::Client::new();
    let resp = client
        .get(format!("http://{}/api/substrate/status", addr))
        .send()
        .await
        .unwrap();

    assert_eq!(resp.status(), StatusCode::OK);
    let status_json: serde_json::Value = resp.json().await.unwrap();
    assert!(status_json.get("hardware").is_some());
    assert!(status_json.get("wasm").is_some());
    assert!(status_json.get("docker").is_some());

    server_task.abort();
}

#[tokio::test]
async fn test_reverse_proxy_gateway_routing() {
    // 1. Start a mock backend API server to receive proxied requests
    let backend_app = Router::new().route(
        "/api/mock-endpoint",
        get(|headers: axum::http::HeaderMap| async move {
            assert!(headers.contains_key("x-forwarded-for"));
            assert_eq!(headers.get("x-forwarded-proto").unwrap(), "http");
            "backend-response-ok"
        }),
    );
    let backend_listener = tokio::net::TcpListener::bind("127.0.0.1:0").await.unwrap();
    let backend_addr = backend_listener.local_addr().unwrap();
    let backend_port = backend_addr.port();

    let backend_server = tokio::spawn(async move {
        axum::serve(backend_listener, backend_app.into_make_service())
            .await
            .unwrap();
    });

    // 2. Start the CLI substrate router pointing its api_port to our mock backend
    let wasi_sandbox = Arc::new(WasiSandbox::new().unwrap());
    let state = Arc::new(AppState {
        api_port: backend_port,
        wasi_sandbox,
        enable_https: false,
    });

    let cli_router = create_router(state);
    let cli_listener = tokio::net::TcpListener::bind("127.0.0.1:0").await.unwrap();
    let cli_addr = cli_listener.local_addr().unwrap();

    let cli_server = tokio::spawn(async move {
        axum::serve(
            cli_listener,
            cli_router.into_make_service_with_connect_info::<SocketAddr>(),
        )
        .await
        .unwrap();
    });

    // 3. Make client request to the CLI proxy and verify the backend response is forwarded back
    let client = reqwest::Client::new();
    let resp = client
        .get(format!("http://{}/api/mock-endpoint", cli_addr))
        .send()
        .await
        .unwrap();

    assert_eq!(resp.status(), StatusCode::OK);
    let body = resp.text().await.unwrap();
    assert_eq!(body, "backend-response-ok");

    backend_server.abort();
    cli_server.abort();
}

#[tokio::test]
async fn test_tls_boundary_init_validations() {
    // Generate temporary files representing certificates to test dual-protocol config compilation
    let cert_pem = rcgen::generate_simple_self_signed(vec!["localhost".to_string()]).unwrap();
    let temp_dir = std::env::temp_dir().join(format!("neurex_tls_{}", uuid_fallback()));
    std::fs::create_dir_all(&temp_dir).unwrap();

    let cert_path = temp_dir.join("cert.pem");
    let key_path = temp_dir.join("key.pem");
    std::fs::write(&cert_path, cert_pem.cert.pem()).unwrap();
    std::fs::write(&key_path, cert_pem.key_pair.serialize_pem()).unwrap();

    // Verify axum-server rustls config loadscert/key files successfully
    let tls_config_res =
        axum_server::tls_rustls::RustlsConfig::from_pem_file(&cert_path, &key_path).await;
    assert!(tls_config_res.is_ok(), "TLS Config compilation must succeed with loaded files");

    let _ = std::fs::remove_dir_all(&temp_dir);
}

fn uuid_fallback() -> String {
    let now = std::time::SystemTime::now()
        .duration_since(std::time::UNIX_EPOCH)
        .unwrap()
        .as_nanos();
    format!("{:x}", now)
}
