#!/bin/bash
# scripts/build-sandbox.sh
# Builds the neurex-sandbox Docker image used by the TesterAgent.
# Run once before `docker compose up`, or when the sandbox Dockerfile changes.
set -e

IMAGE="neurex-sandbox:latest"
CONTEXT="$(dirname "$0")/../neurex-api/sandbox"

echo "🔨 Building sandbox image: ${IMAGE}"
docker build -t "${IMAGE}" "${CONTEXT}"
echo "✅ Sandbox image ready: ${IMAGE}"
echo ""
echo "To verify:"
echo "  docker run --rm --network none -v \$(pwd)/workspace:/workspace:ro ${IMAGE} python --version"
