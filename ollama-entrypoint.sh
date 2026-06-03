#!/bin/bash
# ollama-entrypoint.sh
# Starts Ollama, detects VRAM, and pulls the appropriate model tier.
set -e

PERF_MODEL="${PERF_MODEL:-deepseek-r1:32b}"
BALANCED_MODEL="${BALANCED_MODEL:-qwen2.5-coder:14b}"
LIGHT_MODEL="${LIGHT_MODEL:-qwen2.5-coder:7b}"
EMBED_MODEL="${EMBED_MODEL:-nomic-embed-text}"

echo "🧠 Starting Ollama server..."
ollama serve &
OLLAMA_PID=$!

# Wait for Ollama to be ready
echo "⏳ Waiting for Ollama to become ready..."
until curl -sf http://localhost:11434/api/tags > /dev/null 2>&1; do
  sleep 2
done
echo "✅ Ollama is ready."

# ── VRAM Detection ──────────────────────────────────────────────────────────
detect_vram_gb() {
  if command -v nvidia-smi &>/dev/null; then
    nvidia-smi --query-gpu=memory.total --format=csv,noheader,nounits 2>/dev/null \
      | awk '{s+=$1} END {printf "%d", s/1024}'
  else
    echo "0"
  fi
}

VRAM_GB=$(detect_vram_gb)
echo "🎮 Detected VRAM: ${VRAM_GB} GB"

if [ "$VRAM_GB" -ge 22 ]; then
  TARGET_MODEL="$PERF_MODEL"
  echo "🚀 Performance tier: pulling ${TARGET_MODEL}"
elif [ "$VRAM_GB" -ge 10 ]; then
  TARGET_MODEL="$BALANCED_MODEL"
  echo "⚖️  Balanced tier: pulling ${TARGET_MODEL}"
else
  TARGET_MODEL="$LIGHT_MODEL"
  echo "💡 Light tier: pulling ${TARGET_MODEL}"
fi

# ── Pull models ──────────────────────────────────────────────────────────────
pull_if_missing() {
  local model="$1"
  if ollama list 2>/dev/null | grep -q "^${model}"; then
    echo "✅ Model already present: ${model}"
  else
    echo "📥 Pulling: ${model}..."
    ollama pull "$model"
    echo "✅ Pulled: ${model}"
  fi
}

pull_if_missing "$TARGET_MODEL"
pull_if_missing "$EMBED_MODEL"

# Write selected model to a shared file for the API to read
echo "$TARGET_MODEL" > /tmp/neurex_default_model

echo "🎉 Ollama setup complete. Default model: ${TARGET_MODEL}"

# Hand off to Ollama server process
wait $OLLAMA_PID
