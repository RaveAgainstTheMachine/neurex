# neurex-api/sandbox/Dockerfile
# Minimal sandbox image for the TesterAgent.
# Built from a slim base with common dev toolchains.
# No network access is granted at runtime (--network none in docker run).

FROM python:3.12-slim AS base

# ── Python toolchain ─────────────────────────────────────────────────────────
RUN pip install --no-cache-dir \
    pytest==8.3.3 \
    pytest-asyncio==0.24.0 \
    ruff==0.6.9 \
    mypy==1.11.2 \
    black==24.10.0

# ── Node.js toolchain (for JS/TS projects) ───────────────────────────────────
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl gnupg ca-certificates git \
    && curl -fsSL https://deb.nodesource.com/setup_20.x | bash - \
    && apt-get install -y nodejs \
    && npm install -g typescript eslint prettier \
    && rm -rf /var/lib/apt/lists/*

# ── Go toolchain ──────────────────────────────────────────────────────────────
RUN curl -fsSL https://go.dev/dl/go1.23.2.linux-amd64.tar.gz \
    | tar -C /usr/local -xzf -
ENV PATH="/usr/local/go/bin:$PATH"

# ── Rust toolchain ────────────────────────────────────────────────────────────
RUN curl https://sh.rustup.rs -sSf | sh -s -- -y --default-toolchain stable
ENV PATH="/root/.cargo/bin:$PATH"

# ── Runtime ───────────────────────────────────────────────────────────────────
WORKDIR /workspace

# Non-root user for defense-in-depth
RUN useradd -m -u 1000 sandbox
USER sandbox

CMD ["/bin/bash"]
