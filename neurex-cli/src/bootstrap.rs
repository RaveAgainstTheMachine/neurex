use colored::*;
use std::env::consts::{ARCH, OS};
use std::fs;
use std::io::Cursor;
use std::path::{Path, PathBuf};
use tokio::process::Command;

fn get_uv_target() -> &'static str {
    match (OS, ARCH) {
        ("linux", "x86_64") => "x86_64-unknown-linux-gnu",
        ("linux", "aarch64") => "aarch64-unknown-linux-gnu",
        ("macos", "x86_64") => "x86_64-apple-darwin",
        ("macos", "aarch64") => "aarch64-apple-darwin",
        ("windows", "x86_64") => "x86_64-pc-windows-msvc",
        _ => panic!(
            "Unsupported OS/Architecture combination for Neurex Bootstrapper: {}-{}",
            OS, ARCH
        ),
    }
}

pub async fn ensure_uv() -> PathBuf {
    let home = dirs::home_dir().expect("Failed to locate home directory");
    let neurex_dir = home.join(".neurex");
    let bin_dir = neurex_dir.join("bin");
    fs::create_dir_all(&bin_dir).expect("Failed to create ~/.neurex/bin directory");

    let exe_ext = if OS == "windows" { ".exe" } else { "" };
    let uv_path = bin_dir.join(format!("uv{}", exe_ext));

    if uv_path.exists() {
        return uv_path;
    }

    println!("{} Bootstrapping Hermetic Runtime (uv)...", "[*]".cyan());

    let target = get_uv_target();
    let ext = if OS == "windows" { "zip" } else { "tar.gz" };
    let url = format!(
        "https://github.com/astral-sh/uv/releases/latest/download/uv-{}.{}",
        target, ext
    );

    let client = reqwest::Client::new();
    let response = client
        .get(&url)
        .send()
        .await
        .expect("Failed to download uv runtime");
    let bytes = response.bytes().await.expect("Failed to read uv bytes");

    println!("{} Extracting Runtime Engine...", "[*]".cyan());

    if OS == "windows" {
        let reader = Cursor::new(bytes);
        let mut archive = zip::ZipArchive::new(reader).expect("Failed to read zip");
        for i in 0..archive.len() {
            let mut file = archive.by_index(i).unwrap();
            let outpath = match file.enclosed_name() {
                Some(path) => path.to_owned(),
                None => continue,
            };
            if outpath.file_name().unwrap() == "uv.exe" {
                let mut outfile = fs::File::create(&uv_path).unwrap();
                std::io::copy(&mut file, &mut outfile).unwrap();
                break;
            }
        }
    } else {
        use flate2::read::GzDecoder;
        use tar::Archive;

        let tar = GzDecoder::new(Cursor::new(bytes));
        let mut archive = Archive::new(tar);
        for file in archive.entries().unwrap() {
            let mut file = file.unwrap();
            let path = file.path().unwrap().into_owned();
            if path.file_name().unwrap() == "uv" {
                let mut outfile = fs::File::create(&uv_path).unwrap();
                std::io::copy(&mut file, &mut outfile).unwrap();

                #[cfg(unix)]
                {
                    use std::os::unix::fs::PermissionsExt;
                    let mut perms = fs::metadata(&uv_path).unwrap().permissions();
                    perms.set_mode(0o755);
                    fs::set_permissions(&uv_path, perms).unwrap();
                }
                break;
            }
        }
    }

    println!(
        "  {} Hermetic Engine provisioned at {:?}",
        "✓".green(),
        uv_path
    );
    uv_path
}

pub async fn ensure_env(uv_path: &Path) -> PathBuf {
    let home = dirs::home_dir().unwrap();
    let env_dir = home.join(".neurex").join("env");

    let python_exe = if OS == "windows" {
        env_dir.join("Scripts").join("python.exe")
    } else {
        env_dir.join("bin").join("python")
    };

    if python_exe.exists() {
        return env_dir;
    }

    println!(
        "{} Provisioning Neural Python Environment (3.11)...",
        "[*]".cyan()
    );

    let status = Command::new(uv_path)
        .arg("venv")
        .arg(&env_dir)
        .arg("--python")
        .arg("3.11")
        .status()
        .await
        .expect("Failed to run uv venv");

    if !status.success() {
        panic!("Failed to create Python virtual environment");
    }

    println!("  {} Environment created", "✓".green());
    env_dir
}

pub async fn install_dependencies(uv_path: &Path, env_dir: &Path, req_path: &Path) {
    println!("{} Syncing Neural Weights & API Logic...", "[*]".cyan());

    let status = Command::new(uv_path)
        .arg("pip")
        .arg("install")
        .arg("-r")
        .arg(req_path)
        .env("VIRTUAL_ENV", env_dir)
        .status()
        .await
        .expect("Failed to run uv pip install");

    if !status.success() {
        panic!("Failed to install dependencies");
    }

    println!("  {} Dependencies synchronized", "✓".green());
}
