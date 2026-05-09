use anyhow::{Context, Result, bail};
use std::env::consts::{ARCH, OS};
use std::fs;
use std::io::Cursor;
use std::path::{Path, PathBuf};
use tokio::process::Command;
use tracing::{info, warn};

fn get_uv_target() -> Result<&'static str> {
    match (OS, ARCH) {
        ("linux", "x86_64") => Ok("x86_64-unknown-linux-gnu"),
        ("linux", "aarch64") => Ok("aarch64-unknown-linux-gnu"),
        ("macos", "x86_64") => Ok("x86_64-apple-darwin"),
        ("macos", "aarch64") => Ok("aarch64-apple-darwin"),
        ("windows", "x86_64") => Ok("x86_64-pc-windows-msvc"),
        _ => bail!(
            "Unsupported OS/Architecture combination for Neurex Bootstrapper: {}-{}",
            OS,
            ARCH
        ),
    }
}

pub async fn ensure_uv() -> Result<PathBuf> {
    let home = dirs::home_dir().context("Failed to locate home directory")?;
    let neurex_dir = home.join(".neurex");
    let bin_dir = neurex_dir.join("bin");
    fs::create_dir_all(&bin_dir).context("Failed to create ~/.neurex/bin directory")?;

    let exe_ext = if OS == "windows" { ".exe" } else { "" };
    let uv_path = bin_dir.join(format!("uv{}", exe_ext));

    if uv_path.exists() {
        return Ok(uv_path);
    }

    info!("Bootstrapping Hermetic Runtime (uv)...");

    let target = get_uv_target()?;
    let ext = if OS == "windows" { "zip" } else { "tar.gz" };
    let url =
        format!("https://github.com/astral-sh/uv/releases/latest/download/uv-{}.{}", target, ext);

    let client = reqwest::Client::new();
    let response = client.get(&url).send().await.context("Failed to download uv runtime")?;

    let bytes = response.bytes().await.context("Failed to read uv bytes")?;

    info!("Extracting Runtime Engine...");

    if OS == "windows" {
        let reader = Cursor::new(bytes);
        let mut archive = zip::ZipArchive::new(reader).context("Failed to read zip")?;
        for i in 0..archive.len() {
            let mut file = archive.by_index(i).context("Failed to access zip entry")?;
            let outpath = match file.enclosed_name() {
                Some(path) => path.to_owned(),
                None => continue,
            };
            if outpath.file_name().and_then(|n| n.to_str()) == Some("uv.exe") {
                let mut outfile = fs::File::create(&uv_path).context("Failed to create uv.exe")?;
                std::io::copy(&mut file, &mut outfile).context("Failed to copy uv.exe bytes")?;
                break;
            }
        }
    } else {
        use flate2::read::GzDecoder;
        use tar::Archive;

        let tar = GzDecoder::new(Cursor::new(bytes));
        let mut archive = Archive::new(tar);
        for file in archive.entries().context("Failed to read tar entries")? {
            let mut file = file.context("Failed to access tar entry")?;
            let path = file.path().context("Failed to get tar entry path")?.into_owned();
            if path.file_name().and_then(|n| n.to_str()) == Some("uv") {
                let mut outfile =
                    fs::File::create(&uv_path).context("Failed to create uv binary")?;
                std::io::copy(&mut file, &mut outfile).context("Failed to copy uv binary bytes")?;

                #[cfg(unix)]
                {
                    use std::os::unix::fs::PermissionsExt;
                    let mut perms = fs::metadata(&uv_path)
                        .context("Failed to get uv binary metadata")?
                        .permissions();
                    perms.set_mode(0o755);
                    fs::set_permissions(&uv_path, perms)
                        .context("Failed to set uv binary permissions")?;
                }
                break;
            }
        }
    }

    info!("Hermetic Engine provisioned at {:?}", uv_path);
    Ok(uv_path)
}

pub async fn ensure_env(uv_path: &Path) -> Result<PathBuf> {
    let home = dirs::home_dir().context("Failed to locate home directory")?;
    let env_dir = home.join(".neurex").join("env");

    let python_exe = if OS == "windows" {
        env_dir.join("Scripts").join("python.exe")
    } else {
        env_dir.join("bin").join("python")
    };

    if python_exe.exists() {
        return Ok(env_dir);
    }

    info!("Provisioning Neural Python Environment (3.11)...");

    let status = Command::new(uv_path)
        .arg("venv")
        .arg(&env_dir)
        .arg("--python")
        .arg("3.11")
        .status()
        .await
        .context("Failed to run uv venv")?;

    if !status.success() {
        bail!("Failed to create Python virtual environment");
    }

    info!("Environment created at {:?}", env_dir);
    Ok(env_dir)
}

pub async fn install_dependencies(uv_path: &Path, env_dir: &Path, req_path: &Path) -> Result<()> {
    info!("Syncing Neural Weights & API Logic...");

    if !req_path.exists() {
        warn!("Requirements file NOT FOUND at {:?}. Skipping dependency sync.", req_path);
        return Ok(());
    }

    let status = Command::new(uv_path)
        .arg("pip")
        .arg("install")
        .arg("-r")
        .arg(req_path)
        .env("VIRTUAL_ENV", env_dir)
        .status()
        .await
        .context("Failed to run uv pip install")?;

    if !status.success() {
        bail!("Failed to install dependencies from {:?}", req_path);
    }

    info!("Dependencies synchronized successfully");
    Ok(())
}
