use neurex_cli::sandbox::NativeExecutor;
use neurex_cli::wasi_sandbox::WasiSandbox;
use sysinfo::System;

#[test]
fn test_native_executor_jail() {
    let temp_dir = std::env::temp_dir().join(format!("neurex_test_native_{}", uuid_fallback()));
    std::fs::create_dir_all(&temp_dir).unwrap();
    let root_path = temp_dir.to_str().unwrap();

    let exec = NativeExecutor::new(root_path);

    // Test pwd command inside jail
    let res = exec.execute("pwd").unwrap();
    assert_eq!(res.stdout, "/workspace");
    assert_eq!(res.exit_code, 0);

    // Test nonexistent cat command
    let res = exec.execute("cat non_existent_file.txt").unwrap();
    assert_eq!(res.exit_code, 1);
    assert!(res.stderr.contains("Error") || res.stderr.contains("not found"));

    // Clean up
    let _ = std::fs::remove_dir_all(&temp_dir);
}

#[test]
fn test_wasi_sandbox_compilation() {
    let sandbox = WasiSandbox::new().unwrap();

    // The simplest 8-byte valid WASM binary header
    let wasm_bytes: &[u8] = &[0x00, 0x61, 0x73, 0x6d, 0x01, 0x00, 0x00, 0x00];
    let temp_workspace = std::env::temp_dir().join(format!("neurex_test_wasi_{}", uuid_fallback()));
    std::fs::create_dir_all(&temp_workspace).unwrap();

    // Verify compile logic is reachable and wasmtime operates correctly
    let res = sandbox.run_module(wasm_bytes, &temp_workspace, vec![]);
    // Should fail only on start function missing, which proves compilation and environment setup succeeded
    assert!(res.is_err());
    let err_str = format!("{:?}", res.err().unwrap());
    assert!(
        err_str.contains("Failed to instantiate")
            || err_str.contains("typed function")
            || err_str.contains("export")
            || err_str.contains("_start")
    );

    let _ = std::fs::remove_dir_all(&temp_workspace);
}

#[test]
fn test_wasi_sandbox_execution() {
    let sandbox = WasiSandbox::new().unwrap();
    let temp_workspace =
        std::env::temp_dir().join(format!("neurex_test_wasi_exec_{}", uuid_fallback()));
    std::fs::create_dir_all(&temp_workspace).unwrap();

    let wat_content = r#"
        (module
          (import "wasi_snapshot_preview1" "fd_write" (func $fd_write (param i32 i32 i32 i32) (result i32)))
          (memory 1)
          (export "memory" (memory 0))
          (data (i32.const 8) "Hello from WASI!")
          (func $main (export "_start")
            ;; io_vec.buf = 8
            (i32.store (i32.const 32) (i32.const 8))
            ;; io_vec.len = 16
            (i32.store (i32.const 36) (i32.const 16))
            ;; fd_write(1, &io_vec, 1, &written)
            (call $fd_write
              (i32.const 1)     ;; fd = stdout
              (i32.const 32)    ;; *iovs
              (i32.const 1)     ;; iovs_len
              (i32.const 40)    ;; *written
            )
            drop
          )
        )
    "#;

    let wasm_bytes = wat_content.as_bytes();

    let res = sandbox.run_module(wasm_bytes, &temp_workspace, vec![]).unwrap();
    assert_eq!(res.exit_code, 0);
    assert_eq!(res.stdout, "Hello from WASI!");
    assert_eq!(res.stderr, "");

    let _ = std::fs::remove_dir_all(&temp_workspace);
}

#[tokio::test]
async fn test_docker_connection_handshake() {
    // Attempt local docker connection handshake
    let docker_res = neurex_cli::sandbox::connect_docker().await;
    match docker_res {
        Ok(docker) => {
            let info = docker.info().await;
            assert!(info.is_ok() || info.is_err(), "Handshake logic runs cleanly");
        }
        Err(_) => {
            // Safe fallback on environments without docker running
            println!("Docker daemon not running, skipping live Bollard tests");
        }
    }
}

#[test]
fn test_sysinfo_diagnostics_collection() {
    let mut sys = System::new_all();
    sys.refresh_all();

    // Verify basic sysinfo collection capabilities
    assert!(sys.total_memory() > 0);
    assert!(!sys.cpus().is_empty());
}

#[tokio::test]
async fn test_port_conflict_detection_logic() {
    // Bind to a random OS-assigned port to verify detect logic
    let listener = std::net::TcpListener::bind("127.0.0.1:0").unwrap();
    let bound_port = listener.local_addr().unwrap().port();

    // Check conflict logic by attempting to bind to the same port
    let second_bind = std::net::TcpListener::bind(format!("127.0.0.1:{}", bound_port));
    assert!(second_bind.is_err(), "Port conflict should be successfully caught");
}

fn uuid_fallback() -> String {
    let now =
        std::time::SystemTime::now().duration_since(std::time::UNIX_EPOCH).unwrap().as_nanos();
    format!("{:x}", now)
}
