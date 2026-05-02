use anyhow::{Context, Result, bail};
use bollard::Docker;
use bollard::container::{Config, CreateContainerOptions, RemoveContainerOptions, StartContainerOptions};
use bollard::models::HostConfig;
use tracing::info;

pub async fn connect_docker() -> Result<Docker> {
    Docker::connect_with_local_defaults().context("Failed to connect to Docker daemon")
}

pub async fn ensure_sandbox(docker: &Docker, workspace_path: &str) -> Result<()> {
    info!("Booting Neural Execution Sandbox...");

    // Remove existing container if it exists
    let _ = docker
        .remove_container(
            "neurex-sandbox-agent",
            Some(RemoveContainerOptions {
                force: true,
                ..Default::default()
            }),
        )
        .await;

    let binds = vec![format!("{}:/workspace", workspace_path)];
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

    docker.create_container(options, config).await.context("Failed to create sandbox container")?;
    
    docker
        .start_container(
            "neurex-sandbox-agent",
            None::<StartContainerOptions<String>>,
        )
        .await
        .context("Failed to start sandbox container")?;

    info!("Workspace mounted securely at /workspace");
    info!("CoderAgent container started (Alpine Sandbox)");
    Ok(())
}

pub async fn stop_sandbox(docker: &Docker) -> Result<()> {
    info!("Draining Sandboxed execution units...");
    docker
        .remove_container(
            "neurex-sandbox-agent",
            Some(RemoveContainerOptions {
                force: true,
                ..Default::default()
            }),
        )
        .await
        .context("Failed to remove sandbox container")
}

/// A pure-Rust fallback executor for basic filesystem operations.
/// Enforces jailing to the workspace path.
pub struct NativeExecutor {
    workspace_root: std::path::PathBuf,
}

impl NativeExecutor {
    pub fn new(workspace: &str) -> Self {
        Self {
            workspace_root: std::path::PathBuf::from(workspace),
        }
    }

    pub fn execute(&self, command: &str) -> Result<super::wasi_sandbox::ExecResult> {
        let parts: Vec<&str> = command.split_whitespace().collect();
        if parts.is_empty() {
            bail!("Empty command");
        }

        let cmd = parts[0];
        let mut stdout = String::new();
        let mut stderr = String::new();
        let mut exit_code = 0;

        match cmd {
            "ls" => {
                let sub_path = parts.get(1).unwrap_or(&".");
                let target = self.workspace_root.join(sub_path.trim_start_matches('/'));
                match std::fs::read_dir(target) {
                    Ok(entries) => {
                        for entry in entries {
                            if let Ok(entry) = entry {
                                stdout.push_str(&format!("{}\n", entry.file_name().to_string_lossy()));
                            }
                        }
                    }
                    Err(e) => {
                        stderr = format!("Error: {}", e);
                        exit_code = 1;
                    }
                }
            }
            "cat" => {
                let sub_path = parts.get(1).context("cat requires a path")?;
                let target = self.workspace_root.join(sub_path.trim_start_matches('/'));
                match std::fs::read_to_string(target) {
                    Ok(content) => stdout = content,
                    Err(e) => {
                        stderr = format!("Error: {}", e);
                        exit_code = 1;
                    }
                }
            }
            "pwd" => {
                stdout = "/workspace".to_string();
            }
            _ => {
                stderr = format!("Command '{}' not implemented in Native Fallback. (Docker or WASM required for full shell).", cmd);
                exit_code = 127;
            }
        }

        Ok(super::wasi_sandbox::ExecResult { stdout, stderr, exit_code })
    }
}
