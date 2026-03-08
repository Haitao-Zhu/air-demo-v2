#!/usr/bin/env bash
# Start MCP servers and the AI Refinery FastAPI agent server.
set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$SCRIPT_DIR"

# Load environment variables
if [ -f .env ]; then
    export $(grep -v '^#' .env | xargs)
    echo "Loaded .env"
fi

# Activate shared venv (./venv is a symlink to ../../venv)
source ./venv/bin/activate 2>/dev/null || source ../../venv/bin/activate 2>/dev/null || true

# Kill any leftover processes on our ports
echo "Cleaning up old processes..."
lsof -ti:4001,4003,4004,8000 2>/dev/null | xargs kill -9 2>/dev/null || true
sleep 1

# --- 1. Start DuckDuckGo MCP server (HTTP stream on port 4003) ---
echo "Starting DuckDuckGo MCP server on port 4003..."
python duck_duck_go/duckduckgo_http_server.py --port=4003 &
DDG_PID=$!

for i in $(seq 1 15); do
    if nc -z localhost 4003 2>/dev/null; then
        echo "DuckDuckGo MCP server ready (pid=$DDG_PID)"
        break
    fi
    sleep 1
done

# --- 2. Start arXiv MCP server (SSE proxy on port 4001) ---
echo "Starting arXiv MCP server on port 4001..."
mcp-proxy --port=4001 -- python -m arxiv_mcp_server &
ARXIV_PID=$!

for i in $(seq 1 15); do
    if nc -z localhost 4001 2>/dev/null; then
        echo "arXiv MCP server ready (pid=$ARXIV_PID)"
        break
    fi
    sleep 1
done

# --- 3. Start Filesystem MCP server (SSE proxy on port 4004) ---
echo "Starting Filesystem MCP server on port 4004..."
mcp-proxy --port=4004 -- \
    npx -y @modelcontextprotocol/server-filesystem "$SCRIPT_DIR" &
FS_PID=$!

for i in $(seq 1 15); do
    if nc -z localhost 4004 2>/dev/null; then
        echo "Filesystem MCP server ready (pid=$FS_PID)"
        break
    fi
    sleep 1
done

# --- 4. Start FastAPI web UI server ---
echo "Starting web UI on port 8000..."
echo "Open http://localhost:8000 in your browser"
exec python app_ui.py
