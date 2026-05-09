#!/bin/bash

# scripts/update-loc.sh
# Calculates LOC for Python, TypeScript, and Rust and updates README.md badges.

set -e

# Counts
PY_LOC=$(find . -type f -name "*.py" -not -path "*node_modules*" -not -path "*/.*" -not -path "*venv*" | xargs wc -l | tail -n 1 | awk '{print $1}')
TS_LOC=$(find . -type f \( -name "*.ts" -o -name "*.tsx" \) -not -path "*node_modules*" -not -path "*/.*" -not -path "*venv*" -not -path "*/dist/*" | xargs wc -l | tail -n 1 | awk '{print $1}')
RS_LOC=$(find . -type f -name "*.rs" -not -path "*/.*" -not -path "*/target/*" | xargs wc -l | tail -n 1 | awk '{print $1}')

# Format to "X.Yk" using awk (no bc dependency)
PY_K=$(awk "BEGIN {printf \"%.1f\", $PY_LOC / 1000}")
TS_K=$(awk "BEGIN {printf \"%.1f\", $TS_LOC / 1000}")
RS_K=$(awk "BEGIN {printf \"%.1f\", $RS_LOC / 1000}")

echo "Updating LOC Badges..."
echo "Python: ${PY_K}k"
echo "TypeScript: ${TS_K}k"
echo "Rust: ${RS_K}k"

# Update README.md
sed -i "s/TypeScript-[0-9.]*k%20LOC/TypeScript-${TS_K}k%20LOC/" README.md
sed -i "s/Python-[0-9.]*k%20LOC/Python-${PY_K}k%20LOC/" README.md
sed -i "s/Rust-[0-9.]*k%20LOC/Rust-${RS_K}k%20LOC/" README.md

echo "✅ README.md updated."
