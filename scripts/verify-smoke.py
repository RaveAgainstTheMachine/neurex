#!/usr/bin/env python3
# scripts/verify-smoke.py — Automated verification for Evaluation Parity.
#
# Scans staged git files for core orchestration changes (agents/skills)
# and ensures that smoke tests were also updated. Logs missing smoke tests.

import subprocess
import sys
import os
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

def get_staged_files() -> list[str]:
    try:
        result = subprocess.run(
            ["git", "diff", "--cached", "--name-only"],
            capture_output=True,
            text=True,
            check=True
        )
        return [line.strip() for line in result.stdout.splitlines() if line.strip()]
    except subprocess.CalledProcessError:
        print("❌ Error: Failed to run git diff. Are you in a git repository?")
        sys.exit(1)

def log_missing_smoke_tests(violating_files: list[str]):
    log_dir = ROOT / "eval" / "logs"
    log_dir.mkdir(parents=True, exist_ok=True)
    log_file = log_dir / "missing_smoke_tests.log"
    
    timestamp = datetime.now(timezone.utc).isoformat()
    with open(log_file, "a") as f:
        for vf in violating_files:
            f.write(f"[{timestamp}] Missing smoke test for modified core component: {vf}\n")
    print(f"📝 Logged missing smoke tests to {log_file.relative_to(ROOT)}")

def verify_smoke_parity():
    print("📋 Auditing Evaluation Parity (Smoke Tests)...")
    staged_files = get_staged_files()
    
    # Define core directories that trigger the smoke test requirement
    core_triggers = [
        "neurex-api/core/agents/",
        "neurex-api/core/skills/",
        "neurex-api/core/orchestrator.py"
    ]
    
    # Define files that satisfy the smoke test requirement
    smoke_satisfiers = [
        "neurex-api/tests/test_smoke_evals.py",
        "eval/run_evals.py"
    ]
    
    triggered_files = [f for f in staged_files if any(f.startswith(t) for t in core_triggers)]
    
    if not triggered_files:
        print("   ✓ No core capability modifications detected. Evaluation Parity satisfied.")
        return
        
    print(f"   🔍 Detected modifications to core capabilities: {len(triggered_files)} files")
    
    satisfiers_present = [f for f in staged_files if f in smoke_satisfiers]
    
    if satisfiers_present:
        print("   ✓ Smoke test modifications detected alongside core changes.")
        print("\n✅ Verification successful! Evaluation Parity achieved.")
        sys.exit(0)
    else:
        print("\n❌ ERROR: Evaluation Parity Violation Detected!")
        print("You modified core capabilities without updating the smoke evaluation suite.")
        print("The following core files were modified:")
        for tf in triggered_files:
            print(f"  - {tf}")
        print("\nPer .projectrules, you MUST add or update a smoke evaluation case in:")
        for sf in smoke_satisfiers:
            print(f"  - {sf}")
            
        log_missing_smoke_tests(triggered_files)
        sys.exit(1)

if __name__ == "__main__":
    verify_smoke_parity()
