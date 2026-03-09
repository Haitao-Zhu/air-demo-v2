#!/usr/bin/env bash
# Start MCP servers and the AI Refinery FastAPI agent server.
set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$SCRIPT_DIR"

# Load environment variables
if [ -f .env ]; then
    set -a
    . .env
    set +a
    echo "Loaded .env"
fi

# Activate shared venv
source ./venv/bin/activate 2>/dev/null || source ../venv/bin/activate 2>/dev/null || true

# Kill any leftover processes on our ports (works on both macOS and Linux/WSL)
echo "Cleaning up old processes..."
for port in 4001 4003 4004 8000; do
    if command -v lsof &>/dev/null; then
        lsof -ti:"$port" 2>/dev/null | xargs kill -9 2>/dev/null || true
    elif command -v fuser &>/dev/null; then
        fuser -k "$port"/tcp 2>/dev/null || true
    fi
done
sleep 1

# Helper: wait for a port to become available (works on macOS and Linux/WSL)
wait_for_port() {
    local port=$1 name=$2 pid=$3
    for i in $(seq 1 15); do
        if (echo >/dev/tcp/localhost/"$port") 2>/dev/null; then
            echo "$name ready (pid=$pid)"
            return 0
        fi
        sleep 1
    done
    echo "WARNING: $name may not have started on port $port"
}

# --- 1. Start DuckDuckGo MCP server (HTTP stream on port 4003) ---
echo "Starting DuckDuckGo MCP server on port 4003..."
python duck_duck_go/duckduckgo_http_server.py --port=4003 &
DDG_PID=$!
wait_for_port 4003 "DuckDuckGo MCP server" $DDG_PID

# --- 2. Start arXiv MCP server (SSE proxy on port 4001) ---
echo "Starting arXiv MCP server on port 4001..."
mcp-proxy --port=4001 -- python -m arxiv_mcp_server &
ARXIV_PID=$!
wait_for_port 4001 "arXiv MCP server" $ARXIV_PID

# --- 3. Start Filesystem MCP server (SSE proxy on port 4004) ---
echo "Starting Filesystem MCP server on port 4004..."
mcp-proxy --port=4004 -- \
    npx -y @modelcontextprotocol/server-filesystem "$SCRIPT_DIR" &
FS_PID=$!
wait_for_port 4004 "Filesystem MCP server" $FS_PID

MODE="${1:-ui}"

# --- 4. Start the app ---
if [ "$MODE" = "cli" ]; then
    echo "Starting CLI mode..."
    exec python app_cli.py
else
    echo "Starting web UI on port 8000..."
    echo "Open http://localhost:8000 in your browser"
    exec python app_ui.py
fi
