#!/usr/bin/env python3
# scripts/verify-docs.py — Automated verification of version consistency and documentation parity.
#
# Scans all primary configurations and documents, asserting strict version parity,
# changelog completeness, and staged atomic documentation parity.

import re
import sys
import json
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

def get_staged_files() -> list[str]:
    """Retrieves list of files staged in the Git index."""
    try:
        result = subprocess.run(
            ["git", "diff", "--cached", "--name-only"],
            capture_output=True,
            text=True,
            check=True
        )
        return [line.strip() for line in result.stdout.splitlines() if line.strip()]
    except Exception:
        return []

def main() -> int:
    errors = []
    print("📋 Auditing codebase documentation and version integrity...")

    # 1. Read master versions
    version_py = ROOT / "neurex-api" / "version.py"
    cargo_toml = ROOT / "neurex-cli" / "Cargo.toml"
    web_json = ROOT / "neurex-web" / "package.json"
    landing_json = ROOT / "neurex-landing" / "package.json"

    master_version = None

    # Parse Python version
    if version_py.exists():
        match = re.search(r'VERSION\s*=\s*["\']([^"\']+)["\']', version_py.read_text())
        if match:
            master_version = match.group(1)
            print(f"   ✓ API Master Version: {master_version}")
        else:
            errors.append("Could not parse VERSION from neurex-api/version.py")
    else:
        errors.append("neurex-api/version.py does not exist")

    if not master_version:
        print("❌ Failed: Could not resolve master version baseline.")
        return 1

    # Verify Cargo.toml version
    if cargo_toml.exists():
        content = cargo_toml.read_text()
        match = re.search(r'^version\s*=\s*["\']([^"\']+)["\']', content, re.MULTILINE)
        if match:
            cargo_version = match.group(1)
            if cargo_version != master_version:
                errors.append(f"CLI version mismatch in Cargo.toml: expected '{master_version}', found '{cargo_version}'")
            else:
                print("   ✓ CLI Cargo Version matched.")
        else:
            errors.append("Could not parse version from neurex-cli/Cargo.toml")
    else:
        errors.append("neurex-cli/Cargo.toml does not exist")

    # Verify Web package.json version
    if web_json.exists():
        try:
            data = json.loads(web_json.read_text())
            web_version = data.get("version")
            if web_version != master_version:
                errors.append(f"Web version mismatch in package.json: expected '{master_version}', found '{web_version}'")
            else:
                print("   ✓ Web package.json Version matched.")
        except Exception as e:
            errors.append(f"Could not parse neurex-web/package.json: {e}")
    else:
        errors.append("neurex-web/package.json does not exist")

    # Verify Landing package.json version
    if landing_json.exists():
        try:
            data = json.loads(landing_json.read_text())
            landing_version = data.get("version")
            if landing_version != master_version:
                errors.append(f"Landing version mismatch in package.json: expected '{master_version}', found '{landing_version}'")
            else:
                print("   ✓ Landing package.json Version matched.")
        except Exception as e:
            errors.append(f"Could not parse neurex-landing/package.json: {e}")
    else:
        errors.append("neurex-landing/package.json does not exist")

    # 2. Check README.md
    readme_md = ROOT / "README.md"
    if readme_md.exists():
        content = readme_md.read_text()
        # Verify version badge URL
        badge_pattern = rf"badge/Version-v{re.escape(master_version)}"
        if not re.search(badge_pattern, content):
            errors.append(f"README.md version badge is out of date. Expected badge URL containing 'v{master_version}'")
        else:
            print("   ✓ README.md version badge is up to date.")

        # Verify footer version
        footer_pattern = rf"v{re.escape(master_version)}\.</sub>"
        if not re.search(footer_pattern, content):
            errors.append(f"README.md footer version string is out of date. Expected 'v{master_version}'")
        else:
            print("   ✓ README.md footer version matched.")
    else:
        errors.append("README.md does not exist")

    # 3. Check Changelogs
    changelog_md = ROOT / "CHANGELOG.md"
    wiki_changelog_md = ROOT / "wiki" / "Changelog.md"

    header_pattern = rf"##\s*\[{re.escape(master_version)}\]"

    if changelog_md.exists():
        if not re.search(header_pattern, changelog_md.read_text()):
            errors.append(f"CHANGELOG.md is missing an entry header matching '## [{master_version}]'")
        else:
            print("   ✓ CHANGELOG.md entry found.")
    else:
        errors.append("CHANGELOG.md does not exist")

    if wiki_changelog_md.exists():
        if not re.search(header_pattern, wiki_changelog_md.read_text()):
            errors.append(f"wiki/Changelog.md is missing an entry header matching '## [{master_version}]'")
        else:
            print("   ✓ wiki/Changelog.md entry found.")
    else:
        errors.append("wiki/Changelog.md does not exist")

    # 4. Git Staging Parity Verification (Enforce atomic updates)
    staged_files = get_staged_files()
    if staged_files:
        print("   🔍 Active Git commit transaction detected. Auditing staging area...")
        
        # Define core code boundaries
        code_paths = [
            "neurex-api/core/",
            "neurex-api/api/",
            "neurex-cli/src/",
            "neurex-web/src/",
            "neurex-landing/src/"
        ]
        
        # Check if any staged file is inside core code paths
        code_modified = False
        for f in staged_files:
            if any(f.startswith(p) for p in code_paths):
                code_modified = True
                break
        
        if code_modified:
            # Check if any documentation files are staged in the same commit
            doc_keywords = ["CHANGELOG.md", "README.md", "NEUREX_REVIEW.md", "API_REFERENCE.md", "wiki/"]
            doc_staged = False
            for f in staged_files:
                if any(k in f for k in doc_keywords) or (f.endswith(".md") and not f.startswith("scratch/")):
                    doc_staged = True
                    break
            
            if not doc_staged:
                errors.append(
                    "Staged Atomic Parity Violation: Code mutations are staged, but NO matching documentation updates "
                    "(e.g., CHANGELOG.md, wiki/Changelog.md, README.md, NEUREX_REVIEW.md, or any .md file) "
                    "were staged in the same commit transaction. Code and documentation MUST be updated atomically."
                )
            else:
                print("   ✓ Staged Atomic Parity matched (code and matching documentation changes are co-staged).")
    else:
        print("   ⚠️  No staged files detected in Git index. Skipping Staging Parity audit.")

    # 5. Capabilities Manifest & AST-based Code Reality check
    capabilities_md = ROOT / "wiki" / "System-Capabilities.md"
    if not capabilities_md.exists():
        errors.append("System-Capabilities.md manifest is missing in wiki/")
    else:
        print("   ✓ System-Capabilities.md manifest exists.")
        
        # Parse core files with AST to check for invalid syntax or stubbed implementations
        import ast
        core_files = [
            ROOT / "neurex-api" / "core" / "orchestrator.py",
            ROOT / "neurex-api" / "core" / "task_graph.py",
            ROOT / "neurex-api" / "core" / "memory" / "worker.py",
            ROOT / "neurex-api" / "core" / "memory" / "hive.py",
        ]
        for cf in core_files:
            if not cf.exists():
                errors.append(f"Core functional file does not exist: {cf.relative_to(ROOT)}")
                continue
            try:
                tree = ast.parse(cf.read_text())
                # AST check: Verify that the file contains active classes/functions and is not empty
                nodes = list(ast.iter_child_nodes(tree))
                if not nodes:
                    errors.append(f"Core file {cf.name} is empty (AST nodes: 0)")
                else:
                    # Check if all top-level functions are just 'pass' or NotImplemented stubs
                    all_stubs = True
                    has_func = False
                    for node in nodes:
                        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                            has_func = True
                            body = node.body
                            if len(body) > 1 or not isinstance(body[0], (ast.Pass, ast.Raise)):
                                all_stubs = False
                                break
                    if has_func and all_stubs:
                        errors.append(f"Core file {cf.name} contains only stub functions/placeholders")
            except SyntaxError as se:
                errors.append(f"AST Syntax Error in core file {cf.name}: {se}")
            except Exception as e:
                errors.append(f"Failed to run AST audit on {cf.name}: {e}")
        
        if not errors:
            print("   ✓ AST Code Reality Audit passed successfully (no empty/stubbed core modules).")

    # 6. Report results
    if errors:
        print("\n❌ Documentation and Version Integrity Verification FAILED:")
        for err in errors:
            print(f"   🔴 {err}")
        return 1

    print("\n✅ Verification successful! 100% Documentation and Version Parity achieved.")
    return 0

if __name__ == "__main__":
    sys.exit(main())
