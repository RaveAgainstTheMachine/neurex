"""
core/infrastructure/lifecycle.py
Operational lifecycle management: Backup, Restore, and Rollback.
"""
import asyncio
import os
import zipfile
from datetime import datetime
from pathlib import Path

import structlog

log = structlog.get_logger()

WORKSPACE_PATH = Path(os.getenv("WORKSPACE_PATH", "/workspace"))
BACKUP_DIR     = WORKSPACE_PATH / ".neurex" / "backups"
DB_PATH        = Path("./neurex.db")

async def snapshot_system_state(version: str) -> str:
    """Create a point-in-time snapshot of the database and configuration."""
    BACKUP_DIR.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_path = BACKUP_DIR / f"neurex_v{version}_{timestamp}.zip"
    
    try:
        def create_zip():
            with zipfile.ZipFile(backup_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
                # 1. Backup Database
                if DB_PATH.exists():
                    zipf.write(DB_PATH, arcname="neurex.db")
                
                # 2. Backup Intel and Configs
                intel_path = WORKSPACE_PATH / ".neurex" / "intel.json"
                if intel_path.exists():
                    zipf.write(intel_path, arcname="intel.json")
                    
                # 3. Backup Rules
                rules_path = WORKSPACE_PATH / ".neurex" / "rules.yaml"
                if rules_path.exists():
                    zipf.write(rules_path, arcname="rules.yaml")
        
        await asyncio.to_thread(create_zip)
        log.info("lifecycle.snapshot_created", path=str(backup_path))
        return str(backup_path)
    except Exception as e:
        log.error("lifecycle.snapshot_failed", error=str(e))
        raise

async def rollback_system(backup_name: str) -> str:
    """Restore system state from a specific backup file."""
    backup_path = BACKUP_DIR / backup_name
    if not backup_path.exists():
        raise FileNotFoundError(f"Backup {backup_name} not found.")
        
    try:
        def extract_zip():
            with zipfile.ZipFile(backup_path, 'r') as zipf:
                zipf.extractall(".") # Extract back to root
        
        await asyncio.to_thread(extract_zip)
        log.info("lifecycle.rollback_complete", backup=backup_name)
        return "System state restored successfully."
    except Exception as e:
        log.error("lifecycle.rollback_failed", error=str(e))
        raise

async def list_backups() -> list[dict]:
    """List available system snapshots."""
    if not BACKUP_DIR.exists():
        return []
    
    backups = []
    for f in BACKUP_DIR.glob("*.zip"):
        stat = f.stat()
        backups.append({
            "name": f.name,
            "size": stat.st_size,
            "created_at": datetime.fromtimestamp(stat.st_ctime).isoformat()
        })
    return sorted(backups, key=lambda x: x["created_at"], reverse=True)
