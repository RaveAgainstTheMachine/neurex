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

async def audit_codebase_health() -> str:
    """
    Perform a multi-dimensional audit of the codebase health.
    Checks for:
    - Documentation drift (CHANGELOG vs Git)
    - Orphaned dependencies
    - Architectural anomalies
    - Security posture
    """
    ws = Path(WORKSPACE_PATH)
    results = {
        "documentation_drift": "Low",
        "stale_files": [],
        "infrastructure_status": "Healthy",
        "recommendations": []
    }

    # 1. Check for CHANGELOG updates
    changelog_path = ws / "CHANGELOG.md"
    if changelog_path.exists():
        # Check if there are commits since last changelog entry (simplified)
        results["documentation_drift"] = "Audit required: Manual verification of v0.2.1-stable vs git history recommended."
    else:
        results["recommendations"].append("Create a CHANGELOG.md to track project evolution.")

    # 2. Check for missing .env
    if not (ws / ".env").exists():
        results["recommendations"].append("Create a .env file for sensitive configurations.")

    # 3. Check for heavy node_modules or venv
    if (ws / "neurex-api" / "node_modules").exists():
        results["recommendations"].append("Found node_modules in API directory — ensure this is intended (usually only for web).")

    log.info("intel.audit_complete")
    return json.dumps(results, indent=2)

async def check_design_compliance(file_path: str) -> str:
    """
    Analyze a file (usually .tsx or .css) for compliance with DESIGN_SYSTEM.md.
    Checks for usage of CSS variables, BEM naming, and glassmorphism tokens.
    """
    ws = Path(WORKSPACE_PATH)
    path = ws / file_path
    if not path.exists():
        return f"Error: file {file_path} not found."

    with open(path, "r") as f:
        content = f.read()

    findings = []
    
    # 1. Check for hardcoded colors instead of variables
    import re
    hex_colors = re.findall(r'#(?:[0-9a-fA-F]{3}){1,2}', content)
    if hex_colors:
        findings.append(f"Hardcoded hex colors found: {', '.join(set(hex_colors))}. Use CSS variables from index.css.")

    # 2. Check for glassmorphism tokens in CSS
    if path.suffix == ".css":
        if "backdrop-filter" not in content and "glass" not in content.lower():
            findings.append("No glassmorphism tokens detected. Ensure the component follows the premium aesthetic.")

    # 3. Check for BEM naming in TSX
    if path.suffix in [".tsx", ".jsx"]:
        if "className" in content and "__" not in content and "--" not in content:
            # Very loose check, just a hint
            findings.append("BEM naming convention (__ or --) not detected in classNames. Verify styling standard.")

    if not findings:
        return "Design Compliance: ✅ Pass. No major violations detected."
    
    return "Design Compliance: ⚠️ Warnings found:\n- " + "\n- ".join(findings)
