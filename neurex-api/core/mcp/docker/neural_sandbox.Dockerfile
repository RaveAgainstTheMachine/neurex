# neural_sandbox.Dockerfile
# Optimized sandbox for running the Neurex Neural Harness in isolation.
# Decoupled from any specific vendor CLI to ensure future-proof autonomy.

FROM node:20-slim

# Install essential build tools for potential compilation during harness execution
RUN apt-get update && apt-get install -y \
    python3 \
    make \
    g++ \
    git \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install the Neurex Neural Engine (abstraction layer)
# Note: In a production environment, this would pull from the Neurex mesh registry.
RUN npm install -g @neurex/neural-harness || true

WORKDIR /workspace

# Environment isolation
ENV NEUREX_SANDBOX=true

ENTRYPOINT ["node"]
