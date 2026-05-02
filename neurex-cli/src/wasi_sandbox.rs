use anyhow::{Context, Result};
use std::path::Path;
use wasmtime::*;
use wasmtime_wasi::sync::WasiCtxBuilder;
use tracing::info;
use std::io::{Read, Write};

pub struct WasiSandbox {
    engine: Engine,
}

pub struct ExecResult {
    pub stdout: String,
    pub stderr: String,
    pub exit_code: i32,
}

impl WasiSandbox {
    pub fn new() -> Result<Self> {
        let engine = Engine::default();
        Ok(Self { engine })
    }

    pub fn run_module(&self, wasm_bytes: &[u8], workspace_path: &Path, args: Vec<String>) -> Result<ExecResult> {
        info!("Initializing WASI Sandbox for workspace: {:?}", workspace_path);

        let mut linker = Linker::new(&self.engine);
        wasmtime_wasi::sync::add_to_linker(&mut linker, |s| s)?;

        // Buffers for output capture
        let stdout_pipe = wasi_common::pipe::WritePipe::new_in_memory();
        let stderr_pipe = wasi_common::pipe::WritePipe::new_in_memory();

        // Create WASI context
        let mut builder = WasiCtxBuilder::new();
        builder
            .set_args(&args)?
            .set_stdout(Box::new(stdout_pipe.clone()))
            .set_stderr(Box::new(stderr_pipe.clone()))
            .preopened_dir(
                cap_std::fs::Dir::open_ambient_dir(workspace_path, cap_std::fs::ambient_authority())?,
                "/workspace",
            )?;

        let wasi = builder.build();
        let mut store = Store::new(&self.engine, wasi);
        let module = Module::from_binary(&self.engine, wasm_bytes).context("Failed to compile WASM module")?;
        
        let instance = linker.instantiate(&mut store, &module)?;
        let start = instance.get_typed_func::<(), ()>(&mut store, "_start")?;
        
        let exit_code = match start.call(&mut store, ()) {
            Ok(_) => 0,
            Err(e) => {
                if let Some(exit) = e.downcast_ref::<wasmtime_wasi::I32ExitCode>() {
                    exit.0
                } else {
                    return Err(e);
                }
            }
        };

        // Extract outputs
        let stdout = String::from_utf8_lossy(&stdout_pipe.try_into_inner().unwrap().into_inner()).to_string();
        let stderr = String::from_utf8_lossy(&stderr_pipe.try_into_inner().unwrap().into_inner()).to_string();

        info!("WASI Module execution completed with code {}", exit_code);
        Ok(ExecResult { stdout, stderr, exit_code })
    }
}
