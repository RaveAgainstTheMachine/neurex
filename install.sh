#!/bin/bash
# Neurex Enterprise Installer Bootstrap
set -e

echo -e "\033[1;36m[+] Bootstrapping Neurex Installer Environment...\033[0m"

# Ensure Python3 and venv are available
if ! command -v python3 &> /dev/null; then
    echo "Error: python3 is required to run the installer."
    exit 1
fi

# Create ephemeral virtual environment
VENV_DIR=".neurex-installer-venv"
python3 -m venv $VENV_DIR
source $VENV_DIR/bin/activate

# Install required CLI UI libraries quietly
echo -e "\033[1;34m[+] Fetching terminal UI components...\033[0m"
pip install --quiet --upgrade pip
pip install --quiet rich questionary requests psutil

# Execute the main interactive installer
python3 install.py

# Cleanup
deactivate
rm -rf $VENV_DIR
