# neurex-claude-sandbox.Dockerfile
# Optimized sandbox for running Claude Code harness in isolation.
FROM node:20-slim

# Install basic dependencies
RUN apt-get update && apt-get install -y \
    git \
    curl \
    python3 \
    make \
    g++ \
    && rm -rf /var/lib/apt/lists/*

# Install Claude Code globally
RUN npm install -g @anthropic-ai/claude-code

# Set workspace
WORKDIR /workspace

# Default entrypoint
ENTRYPOINT ["claude"]
