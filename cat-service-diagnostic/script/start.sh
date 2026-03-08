#!/bin/bash
# start.sh - Automated setup and run for cat-service-diagnostic
# Target: Azure VM running Windows WSL (Ubuntu)
# Usage: bash script/start.sh [cli|ui]
set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
VENV_DIR="$PROJECT_DIR/venv"

MODE="${1:-ui}"

echo "=== Cat Service Diagnostic - Setup & Start ==="
echo "Project dir: $PROJECT_DIR"
echo "Mode: $MODE"
echo ""

# --- 1. System dependencies ---
if ! command -v python3 &>/dev/null; then
    echo ">>> Installing Python3..."
    sudo apt-get update && sudo apt-get install -y python3 python3-pip python3-venv
else
    echo ">>> Python3 found: $(python3 --version)"
fi

# --- 2. Create venv if missing ---
if [ ! -d "$VENV_DIR" ]; then
    echo ">>> Creating virtual environment at $VENV_DIR..."
    python3 -m venv "$VENV_DIR"
else
    echo ">>> Virtual environment already exists."
fi

# Remove the old symlink to ../venv if it exists (was for the original Mac layout)
if [ -L "$PROJECT_DIR/venv" ] && [ "$(readlink "$PROJECT_DIR/venv")" = "../venv" ]; then
    echo ">>> Removing stale venv symlink..."
    rm "$PROJECT_DIR/venv"
    echo ">>> Creating local venv..."
    python3 -m venv "$VENV_DIR"
fi

source "$VENV_DIR/bin/activate"

# --- 3. Install Python dependencies ---
echo ">>> Installing Python packages..."
pip install --upgrade pip -q
pip install \
    "airefinery-sdk==1.27.0" \
    "fastapi==0.135.1" \
    "uvicorn==0.41.0" \
    "python-dotenv==1.2.2" \
    "pandas==3.0.1"

# --- 4. Verify ---
echo ">>> Verifying installation..."
python3 -c "from air import AsyncAIRefinery; print('  airefinery-sdk OK')"
python3 -c "import fastapi, uvicorn, pandas, dotenv; print('  All dependencies OK')"

# --- 5. Run ---
cd "$PROJECT_DIR"

if [ "$MODE" = "cli" ]; then
    echo ""
    echo "=== Starting CLI mode ==="
    python3 app_cli.py
else
    echo ""
    echo "=== Starting Web UI on http://0.0.0.0:8000 ==="
    python3 app_ui.py
fi
