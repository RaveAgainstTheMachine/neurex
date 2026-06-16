#!/usr/bin/env python3
import re
import sys
import os

# Files to check and the regex to extract the version
FILES_TO_CHECK = {
    "neurex-cli/Cargo.toml": r'^version\s*=\s*"([^"]+)"',
    "README.md": r'badge/Version-v([0-9\.]+)-blueviolet',
    "ROADMAP.md": r'Current Version.*`v([0-9\.]+)`',
    "wiki/System-Capabilities.md": r'Neurex `v([0-9\.]+)`',
    "wiki/Installation.md": r'Neurex v([0-9\.]+)',
}

def main():
    root_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    versions = {}
    errors = False

    for rel_path, pattern in FILES_TO_CHECK.items():
        file_path = os.path.join(root_dir, rel_path)
        if not os.path.exists(file_path):
            print(f"ERROR: File not found: {rel_path}")
            errors = True
            continue

        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()
            
        match = re.search(pattern, content, re.MULTILINE)
        if match:
            versions[rel_path] = match.group(1)
        else:
            print(f"ERROR: Could not find version string in {rel_path} using pattern '{pattern}'")
            errors = True

    if not versions:
        print("ERROR: No versions found.")
        sys.exit(1)

    unique_versions = set(versions.values())
    if len(unique_versions) > 1:
        print("ERROR: Version drift detected!")
        for path, ver in versions.items():
            print(f"  {path}: {ver}")
        errors = True
    else:
        print(f"✅ Version check passed: All files at v{list(unique_versions)[0]}")

    if errors:
        sys.exit(1)

if __name__ == "__main__":
    main()
