#!/bin/bash
# scripts/build-sandbox.sh
set -e

echo "Building Neurex Sandbox..."
docker build -t neurex-sandbox:latest ./neurex-sandbox
echo "✅ Sandbox built successfully."
