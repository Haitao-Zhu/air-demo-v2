#!/bin/bash
# start.sh - Run cat-service-diagnostic demo
# Usage: bash script/start.sh [cli|ui]
set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
VENV_DIR="$PROJECT_DIR/../venv"

MODE="${1:-ui}"

# Check venv exists
if [ ! -d "$VENV_DIR" ]; then
    echo "Virtual environment not found at $VENV_DIR"
    echo "Run 'bash setup.sh' from the repo root first."
    exit 1
fi

source "$VENV_DIR/bin/activate"
cd "$PROJECT_DIR"

if [ "$MODE" = "cli" ]; then
    echo "=== Starting CLI mode ==="
    python app_cli.py
else
    echo "=== Starting Web UI on http://0.0.0.0:8000 ==="
    python app_ui.py
fi
