# Onboarding Guide — Manual Environment Setup

This guide documents each step that `setup.sh` performs automatically. Use it if the script fails on your environment (restricted apt repos, missing sudo, corporate proxy, etc.).

---

## Prerequisites

- Windows WSL with Ubuntu (20.04, 22.04, or 24.04)
- Internet access (for pip and npm packages)
- `sudo` access (optional — only needed if Python or Node.js are not pre-installed)

---

## Step 1 — Verify Python 3.10+

The demos require Python 3.10 or higher.

```bash
python3 --version
```

If the version is 3.10+, skip to Step 2.

**If Python is too old or missing:**

```bash
sudo apt update
sudo apt install -y python3.12 python3.12-venv
```

If `apt` is blocked (403 Forbidden, PPA errors), check if a newer Python is already available under a versioned name:

```bash
python3.12 --version
python3.11 --version
python3.10 --version
```

Use whichever is available. If none exist, contact your IT team or download from [python.org](https://www.python.org/downloads/).

---

## Step 2 — Create Virtual Environment

```bash
cd air-demo-v2
python3 -m venv venv
source venv/bin/activate
```

**Common issue — `ensurepip is not available`:**

```bash
# Replace 3.12 with your actual Python version
sudo apt install -y python3.12-venv
python3 -m venv venv
source venv/bin/activate
```

**If the venv gets corrupted** (e.g., `ImportError` on basic packages like `pydantic`):

```bash
rm -rf venv
python3 -m venv venv
source venv/bin/activate
pip install --no-cache-dir -r requirements.txt
```

---

## Step 3 — Install Python Packages

```bash
pip install --upgrade pip
pip install -r requirements.txt
```

**Behind a corporate proxy:**

```bash
pip install --proxy http://your-proxy:port -r requirements.txt
```

**If a specific package fails with corruption or build errors:**

```bash
pip install --force-reinstall --no-cache-dir <package-name>
```

**Verify the installation:**

```bash
python -c "from air import AsyncAIRefinery; print('airefinery-sdk ... OK')"
python -c "import fastapi, uvicorn, pandas, pydantic; print('Core packages ... OK')"
python -c "import fastmcp, httpx, bs4, mcp; print('MCP packages  ... OK')"
```

All three lines should print `OK`. If any fails, reinstall the failing package with `--force-reinstall --no-cache-dir`.

---

## Step 4 — Install Node.js (marketing-agents-v2 only)

The marketing-agents-v2 demo uses MCP servers that require `npx` (part of Node.js). All other demos work without Node.js.

```bash
# Option A: NodeSource (recommended, gives Node 20.x)
curl -fsSL https://deb.nodesource.com/setup_20.x | sudo -E bash -
sudo apt install -y nodejs

# Option B: Ubuntu default packages (older but functional)
sudo apt install -y nodejs npm
```

**Verify:**

```bash
node --version    # v18+ or v20+
npx --version
```

If you cannot install Node.js, skip this step — all demos except marketing-agents-v2 will work.

---

## Post-Setup — Running a Demo

```bash
source venv/bin/activate
cd <demo-directory>
python app_ui.py
# Open http://localhost:8000
```

For marketing-agents-v2, use `bash start.sh` (or `bash start.sh cli` for terminal mode) instead of `python app_ui.py`.

---

## Troubleshooting Reference

| Problem | Cause | Fix |
|---------|-------|-----|
| `\r': command not found` | Windows CRLF line endings | `git config core.autocrlf input && git checkout .` |
| `apt` 403 Forbidden | Corporate firewall blocking Ubuntu repos | Use pre-installed Python; skip `apt` |
| `ensurepip is not available` | Missing venv module | `sudo apt install -y python3.X-venv` |
| `ModuleNotFoundError` | venv not activated | `source ../venv/bin/activate` |
| `ImportError` on a basic package | Corrupted pip cache or venv | `pip install --force-reinstall --no-cache-dir <pkg>` or rebuild venv |
| `pip install` hangs or times out | Corporate proxy | `pip install --proxy http://proxy:port ...` |
| `npx: command not found` | Node.js not installed | Step 4 above (only needed for marketing-agents-v2) |
| Port already in use (e.g., 8000) | Previous process still running | `fuser -k 8000/tcp` or `kill $(lsof -ti:8000)` |
| Web UI not accessible from Windows | WSL networking | Find WSL IP with `hostname -I`, open `http://<ip>:8000` |
| Azure agents fail with RBAC error | Missing Azure AI Developer role | The demo auto-falls back to non-Azure agents; no action needed |
| `pandas` or `dateutil` ImportError | Broken `python-dateutil` | `pip install --force-reinstall "python-dateutil==2.8.2"` |
