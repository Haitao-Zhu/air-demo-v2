#!/bin/bash
# setup.sh - One-time environment setup for all AI Refinery demos
# Target: Windows WSL (Ubuntu)
# Usage: bash setup.sh
set -e

REPO_DIR="$(cd "$(dirname "$0")" && pwd)"
VENV_DIR="$REPO_DIR/venv"

echo "============================================"
echo "  AI Refinery Demo - Environment Setup"
echo "============================================"
echo ""

# --- 1. Find or install Python 3.12+ ---
PYTHON_CMD=""
for ver in python3.13 python3.12 python3.11 python3.10 python3; do
    if command -v "$ver" &>/dev/null; then
        PYTHON_CMD="$ver"
        break
    fi
done

if [ -z "$PYTHON_CMD" ]; then
    echo ">>> Python 3.10+ not found. Installing Python 3.12..."
    sudo apt update -y
    sudo apt install -y software-properties-common
    sudo add-apt-repository -y ppa:deadsnakes/ppa
    sudo apt update -y
    sudo apt install -y python3.12 python3.12-venv python3.12-dev
    PYTHON_CMD="python3.12"
fi

echo ">>> [1/4] Using $PYTHON_CMD ($($PYTHON_CMD --version 2>&1))"

# Ensure pip and venv modules are available BEFORE creating venv
PY_VER=$("$PYTHON_CMD" -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')")
NEED_APT=false
if ! "$PYTHON_CMD" -m pip --version &>/dev/null; then NEED_APT=true; fi
if ! "$PYTHON_CMD" -m venv --help &>/dev/null; then NEED_APT=true; fi

if [ "$NEED_APT" = true ]; then
    echo ">>> Installing pip and venv packages..."
    sudo apt update -y
    sudo apt install -y "python${PY_VER}-pip" "python${PY_VER}-venv" python3-pip 2>/dev/null || true
fi

# --- 2. Create virtual environment ---
if [ -L "$VENV_DIR" ]; then
    rm "$VENV_DIR"
fi

# Remove broken venv (e.g. from a previous failed attempt)
if [ -d "$VENV_DIR" ] && [ ! -f "$VENV_DIR/bin/activate" ]; then
    echo ">>> Removing broken virtual environment..."
    rm -rf "$VENV_DIR"
fi

if [ -d "$VENV_DIR" ]; then
    echo ">>> [2/4] Virtual environment already exists at $VENV_DIR"
else
    echo ">>> [2/4] Creating virtual environment..."
    "$PYTHON_CMD" -m venv "$VENV_DIR"
fi

source "$VENV_DIR/bin/activate"

# --- 3. Install Python packages ---
echo ">>> [3/4] Installing Python packages..."
pip install --upgrade pip -q
pip install -r "$REPO_DIR/requirements.txt"

# --- 4. Node.js (for marketing-agents-v2 MCP servers) ---
if command -v node &>/dev/null; then
    echo ">>> [4/4] Node.js already installed: $(node --version)"
elif command -v npx &>/dev/null; then
    echo ">>> [4/4] npx already available"
else
    echo ">>> [4/4] Installing Node.js..."
    if command -v curl &>/dev/null; then
        curl -fsSL https://deb.nodesource.com/setup_20.x | sudo -E bash - && sudo apt install -y nodejs
    else
        sudo apt install -y nodejs npm 2>/dev/null || echo "WARNING: Could not install Node.js. marketing-agents-v2 will not work."
    fi
fi

# --- Verify ---
echo ""
echo ">>> Verifying installation..."
"$VENV_DIR/bin/python" -c "from air import AsyncAIRefinery; print('  airefinery-sdk ... OK')"
"$VENV_DIR/bin/python" -c "import fastapi, uvicorn, pandas, dotenv, tqdm, pydantic; print('  Core packages ... OK')"
"$VENV_DIR/bin/python" -c "import fastmcp, httpx, bs4, mcp; print('  MCP packages  ... OK')"
if command -v node &>/dev/null; then
    echo "  Node.js        ... $(node --version)"
fi

echo ""
echo "============================================"
echo "  Setup complete!"
echo ""
echo "  To run a demo:"
echo "    cd <demo-directory>"
echo "    source ../venv/bin/activate"
echo "    python app_ui.py"
echo "============================================"
