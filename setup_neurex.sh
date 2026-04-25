#!/bin/bash
# setup_neurex.sh — Optimized for /games/AI storage and local binaries
set -e

AI_ROOT="/games/AI"
BIN_DIR="$AI_ROOT/bin"
OLLAMA_MODELS="$AI_ROOT/ollama_models"
CHROMA_DB="$AI_ROOT/chroma_db"

export PATH="$BIN_DIR:$PATH"

echo "🛠️  Starting Neurex Setup..."

# 1. Ensure Directories exist
mkdir -p "$OLLAMA_MODELS" "$CHROMA_DB" "$BIN_DIR"

# 2. Ensure .env exists
if [ ! -f .env ]; then
    echo "📄 Creating .env..."
    cat <<EOF > .env
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODELS=$OLLAMA_MODELS
CHROMA_DB_DIR=$CHROMA_DB
WORKSPACE_PATH=$(pwd)
API_TOKEN=neurex-dev-token
DEFAULT_MODEL=qwen2.5-coder:14b
EMBED_MODEL=nomic-embed-text
LOG_LEVEL=info
EOF
fi

# 3. Start Ollama if not running
if ! pgrep ollama > /dev/null; then
    echo "🧠 Starting Ollama server..."
    OLLAMA_MODELS="$OLLAMA_MODELS" nohup "$BIN_DIR/ollama" serve > "$AI_ROOT/ollama.log" 2>&1 &
    sleep 5
fi

# 4. Pull required models
echo "📥 Ensuring models are present..."
"$BIN_DIR/ollama" pull nomic-embed-text
"$BIN_DIR/ollama" pull qwen2.5-coder:14b
"$BIN_DIR/ollama" pull deepseek-r1:14b

echo "🚀 Environment Ready!"
echo "To start the backend: cd neurex-api && source venv/bin/activate && python main.py"
echo "To start the frontend: cd neurex-web && npm run dev"
