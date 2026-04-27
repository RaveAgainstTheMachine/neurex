"""
core/mcp/tools/intel.py
Intelligence and project-education tools for Neurex.
"""
import os
import json
import structlog
from pathlib import Path

log = structlog.get_logger()

WORKSPACE_PATH = os.getenv("WORKSPACE_PATH", "/workspace")

async def synthesize_project_intel() -> str:
    """
    Analyze project documentation and source code to generate a
    NEUREX_INTEL.json file. This file serves as a 'brain' for agents
    to understand project-specific patterns, rules, and architecture.
    """
    ws = Path(WORKSPACE_PATH)
    intel = {
        "project_name": ws.name,
        "architecture_patterns": [],
        "coding_standards": [],
        "tech_stack": [],
        "critical_files": []
    }
    
    # 1. Tech Stack Detection
    if (ws / "package.json").exists(): intel["tech_stack"].append("TypeScript/Node.js")
    if (ws / "requirements.txt").exists(): intel["tech_stack"].append("Python")
    if (ws / "docker-compose.yml").exists(): intel["tech_stack"].append("Docker/Microservices")

    # 2. Pattern Analysis (Greedy Documentation Search)
    doc_files = ["README.md", "ARCHITECTURE.md", "CONTRIBUTING.md", "FEATURES.md"]
    for doc in doc_files:
        path = ws / doc
        if path.exists():
            with open(path, "r") as f:
                content = f.read().lower()
                # Simple keyword extraction
                if "fastapi" in content: intel["architecture_patterns"].append("FastAPI/REST")
                if "react" in content: intel["architecture_patterns"].append("React/Frontend")
                if "sqlite" in content: intel["architecture_patterns"].append("SQLite Persistence")
                if "totp" in content or "mfa" in content: intel["coding_standards"].append("MFA Security")
                if "ruff" in content: intel["coding_standards"].append("Ruff Linting")

    # 3. Critical File Mapping
    potential_critical = [
        "main.py", "app.py", "src/App.tsx", "core/task_graph.py", 
        "api/routes/auth.py", "neurex-api/main.py"
    ]
    for p in potential_critical:
        if (ws / p).exists():
            intel["critical_files"].append(p)

    # 4. Save Intel
    intel_path = ws / ".neurex" / "intel.json"
    intel_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(intel_path, "w") as f:
        json.dump(intel, f, indent=2)
        
    log.info("intel.synthesized", path=str(intel_path))
    
    return f"Project Intelligence Synthesized and saved to {intel_path.relative_to(ws)}.\n\n" + \
           f"Detected Stack: {', '.join(intel['tech_stack'])}\n" + \
           f"Active Patterns: {', '.join(intel['architecture_patterns'])}"

async def query_project_intel() -> str:
    """Read the synthesized project intelligence."""
    intel_path = Path(WORKSPACE_PATH) / ".neurex" / "intel.json"
    if not intel_path.exists():
        return "No project intelligence found. Please run 'synthesize_project_intel' first."
    
    with open(intel_path, "r") as f:
        return f.read()
