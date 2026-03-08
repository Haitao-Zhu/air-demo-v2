#!/bin/bash
# setup.sh - One-time environment setup for all AI Refinery demos
# Target: Fresh Windows WSL (Ubuntu)
# Usage: bash setup.sh
set -e

REPO_DIR="$(cd "$(dirname "$0")" && pwd)"
VENV_DIR="$REPO_DIR/venv"
PYTHON_VERSION="3.13"
PYTHON_CMD="python${PYTHON_VERSION}"

echo "============================================"
echo "  AI Refinery Demo - Environment Setup"
echo "============================================"
echo ""

# --- 1. System packages ---
echo ">>> [1/5] Installing system dependencies..."
sudo apt update -y
sudo apt install -y software-properties-common curl git

# --- 2. Python 3.13 via deadsnakes PPA ---
if command -v "$PYTHON_CMD" &>/dev/null; then
    echo ">>> [2/5] $PYTHON_CMD already installed: $($PYTHON_CMD --version)"
else
    echo ">>> [2/5] Installing $PYTHON_CMD from deadsnakes PPA..."
    sudo add-apt-repository -y ppa:deadsnakes/ppa
    sudo apt update -y
    sudo apt install -y "python${PYTHON_VERSION}" "python${PYTHON_VERSION}-venv" "python${PYTHON_VERSION}-dev"
fi

# Ensure venv and distutils packages are present (deadsnakes ships them separately)
sudo apt install -y "python${PYTHON_VERSION}-venv" 2>/dev/null || true

# --- 3. Create virtual environment ---
if [ -L "$VENV_DIR" ]; then
    echo ">>> Removing stale venv symlink..."
    rm "$VENV_DIR"
fi

if [ -d "$VENV_DIR" ]; then
    echo ">>> [3/5] Virtual environment already exists at $VENV_DIR"
else
    echo ">>> [3/5] Creating virtual environment..."
    "$PYTHON_CMD" -m venv "$VENV_DIR"
fi

source "$VENV_DIR/bin/activate"

# --- 4. Install pip and Python packages ---
echo ">>> [4/5] Installing Python packages..."
pip install --upgrade pip -q
pip install -r "$REPO_DIR/requirements.txt"

# --- 5. Node.js (for marketing-agents-v2 MCP servers) ---
if command -v node &>/dev/null; then
    echo ">>> [5/5] Node.js already installed: $(node --version)"
else
    echo ">>> [5/5] Installing Node.js 20.x..."
    curl -fsSL https://deb.nodesource.com/setup_20.x | sudo -E bash -
    sudo apt install -y nodejs
fi

# --- Verify ---
echo ""
echo ">>> Verifying installation..."
"$VENV_DIR/bin/python" -c "from air import AsyncAIRefinery; print('  airefinery-sdk ... OK')"
"$VENV_DIR/bin/python" -c "import fastapi, uvicorn, pandas, dotenv, tqdm, pydantic; print('  Core packages ... OK')"
"$VENV_DIR/bin/python" -c "import fastmcp, httpx, bs4, mcp; print('  MCP packages  ... OK')"
echo "  Node.js        ... $(node --version)"

echo ""
echo "============================================"
echo "  Setup complete!"
echo ""
echo "  To run a demo:"
echo "    cd <demo-directory>"
echo "    source ../venv/bin/activate"
echo "    python app_ui.py"
echo "============================================"
