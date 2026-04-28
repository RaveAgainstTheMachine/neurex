#!/bin/bash

# ⬡ NEUREX MASTER LAUNCHER
# The entry point for the Agentic Operating System.

set -e

# Colors for professional output
PURPLE='\033[0;35m'
CYAN='\033[0;36m'
GREEN='\033[0;32m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${PURPLE}Starting Neurex Mesh Hub...${NC}"

# Check for Docker
if ! [ -x "$(command -v docker)" ]; then
  echo -e "${RED}Error: Docker is not installed.${NC}" >&2
  exit 1
fi

# Hardware Acceleration Detection
if command -v nvidia-smi &> /dev/null; then
    echo -e "${GREEN}NVIDIA GPU detected. CUDA acceleration enabled.${NC}"
elif command -v rocm-smi &> /dev/null; then
    echo -e "${GREEN}AMD GPU detected. ROCm acceleration enabled.${NC}"
elif command -v xpu-smi &> /dev/null || clinfo &> /dev/null; then
    echo -e "${GREEN}Intel/OpenCL GPU detected. SYCL/OpenCL acceleration enabled.${NC}"
else
    echo -e "${CYAN}Note: No dedicated GPU detected via standard drivers. Defaulting to optimized CPU/Shared-Memory mode.${NC}"
fi

# Health Check / Setup
echo -e "${CYAN}Performing System Health Check...${NC}"

# Check if containers are already running
if [ "$(docker ps -q -f name=neurex-api)" ]; then
    echo -e "${GREEN}Neurex is already running. Refreshing logs...${NC}"
    docker compose logs -f --tail 100
    exit 0
fi

# Determine Docker Compose command
if docker compose version &> /dev/null; then
    DOCKER_COMPOSE="docker compose"
elif docker-compose --version &> /dev/null; then
    DOCKER_COMPOSE="docker-compose"
else
    echo -e "${RED}Error: Docker Compose is not installed.${NC}" >&2
    exit 1
fi

# Launch
echo -e "${PURPLE}Deploying Local Swarm...${NC}"
$DOCKER_COMPOSE up -d

echo -e ""
echo -e "  ⬡ ${GREEN}NEUREX IS ONLINE${NC}"
echo -e "  --------------------------------"
echo -e "  Frontend:  ${CYAN}http://localhost:3000${NC}"
echo -e "  API:       ${CYAN}http://localhost:8000${NC}"
echo -e "  Mesh Port: ${CYAN}http://localhost:5000 (RPC)${NC}"
echo -e "  --------------------------------"
echo -e ""

# Tail logs
$DOCKER_COMPOSE logs -f --tail 50
