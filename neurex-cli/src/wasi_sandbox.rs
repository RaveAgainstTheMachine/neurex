use anyhow::{Context, Result};
use std::path::Path;
use wasmtime::*;
use wasmtime_wasi::p1::{self, WasiP1Ctx};
use wasmtime_wasi::p2::pipe::MemoryOutputPipe;
use wasmtime_wasi::{DirPerms, FilePerms, WasiCtxBuilder};

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

    pub fn run_module(
        &self,
        wasm_bytes: &[u8],
        workspace_path: &Path,
        args: Vec<String>,
    ) -> Result<ExecResult> {
        let mut linker: Linker<WasiP1Ctx> = Linker::new(&self.engine);
        p1::add_to_linker_sync(&mut linker, |s| s)?;

        let stdout_pipe = MemoryOutputPipe::new(8192);
        let stderr_pipe = MemoryOutputPipe::new(8192);

        let mut builder = WasiCtxBuilder::new();
        builder.inherit_env().stdout(stdout_pipe.clone()).stderr(stderr_pipe.clone()).args(&args);

        builder.preopened_dir(workspace_path, "/workspace", DirPerms::all(), FilePerms::all())?;

        let wasi = builder.build_p1();
        let mut store = Store::new(&self.engine, wasi);
        let module = Module::new(&self.engine, wasm_bytes)
            .map_err(|e| anyhow::anyhow!(e))
            .context("Failed to compile WASM module")?;

        let instance = linker.instantiate(&mut store, &module)?;
        let start = instance.get_typed_func::<(), ()>(&mut store, "_start")?;

        let run_res = start.call(&mut store, ());
        let exit_code = match run_res {
            Ok(_) => 0,
            Err(e) => {
                // If it exited with a WASI exit code, extract it
                if let Some(status) = e.downcast_ref::<wasmtime_wasi::I32Exit>() {
                    status.0
                } else {
                    1
                }
            }
        };

        let stdout_bytes = stdout_pipe.contents();
        let stderr_bytes = stderr_pipe.contents();
        let stdout = String::from_utf8_lossy(&stdout_bytes).into_owned();
        let stderr = String::from_utf8_lossy(&stderr_bytes).into_owned();

        Ok(ExecResult { stdout, stderr, exit_code })
    }
}
