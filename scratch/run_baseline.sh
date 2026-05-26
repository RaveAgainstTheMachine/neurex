#!/bin/bash
set -e

# Kill any existing uvicorn
pkill -f uvicorn || true

# Start API
cd /games/CodeProjects/AntiGravity/Neurex/neurex/neurex-api
export NEUREX_MOCK_LLM=true
export WORKSPACE_PATH=$(pwd)
./.venv/bin/uvicorn main:app --port 8000 > api.log 2>&1 &
API_PID=$!

echo "Waiting for API to start..."
sleep 15

# Check if API is alive
if ! curl -s http://localhost:8000/health; then
  echo "API failed to start. Logs:"
  cat api.log
  kill $API_PID || true
  exit 1
fi

echo "API is up. Generating auth token..."
TOKEN=$(./.venv/bin/python ../scratch/gen_token.py)
echo "Running evals with token..."
export API_TOKEN=$TOKEN
./.venv/bin/python ../eval/run_evals.py --only smoke

# Cleanup
kill $API_PID || true
echo "Done."
