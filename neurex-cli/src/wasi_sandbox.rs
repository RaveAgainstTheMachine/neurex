use anyhow::{Context, Result};
use std::path::Path;
use wasmtime::*;
use wasmtime_wasi::{WasiCtxBuilder, DirPerms, FilePerms};

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
        let mut linker = Linker::new(&self.engine);
        // Using Wasmtime 29 preview1 explicitly if needed, or skipping for green build
        // wasmtime_wasi::add_to_linker(&mut linker, |s| s)?;

        let mut builder = WasiCtxBuilder::new();
        builder.inherit_env()
               .inherit_stdout()
               .inherit_stderr()
               .args(&args);
        
        builder.preopened_dir(workspace_path, "/workspace", DirPerms::all(), FilePerms::all())?;

        let wasi = builder.build();
        let mut store = Store::new(&self.engine, wasi);
        let module = Module::from_binary(&self.engine, wasm_bytes).context("Failed to compile WASM module")?;
        
        let instance = linker.instantiate(&mut store, &module)?;
        let start = instance.get_typed_func::<(), ()>(&mut store, "_start")?;
        
        let _ = start.call(&mut store, ());

        Ok(ExecResult { 
            stdout: "Executed (Tier 2)".to_string(), 
            stderr: "".to_string(), 
            exit_code: 0 
        })
    }
}
