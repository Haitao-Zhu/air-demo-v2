# AI Refinery Demo Collection

A collection of demo applications built on the **AI Refinery SDK**, showcasing agentic AI patterns including multi-agent orchestration, conditional routing, human-in-the-loop, RAI guardrails, MCP integration, and more.

---

## Environment Setup (Windows WSL)

### Quick Setup (Recommended)

```bash
git clone https://github.com/Haitao-Zhu/air-demo-v2.git
cd air-demo-v2
bash setup.sh
```

`setup.sh` performs the 4 steps below automatically. If it fails at any step, follow the manual instructions for that step and continue.

### Manual Setup (Step-by-Step)

If `setup.sh` does not work on your environment (e.g., restricted apt repos, missing sudo, corporate proxy), follow these steps manually.

#### Step 1 — Verify Python 3.10+

The demos require Python 3.10 or higher. Check what is available:

```bash
python3 --version
```

If the version is 3.10+, you are good. If not, install it:

```bash
sudo apt update
sudo apt install -y python3.12 python3.12-venv
```

If `apt` is blocked, ask your IT team for a Python 3.10+ installation or download from [python.org](https://www.python.org/downloads/).

#### Step 2 — Create Virtual Environment

```bash
cd air-demo-v2
python3 -m venv venv
source venv/bin/activate
```

If you get `ensurepip is not available`, install the venv module:

```bash
# Replace 3.12 with your Python version
sudo apt install -y python3.12-venv
python3 -m venv venv
source venv/bin/activate
```

#### Step 3 — Install Python Packages

```bash
pip install --upgrade pip
pip install -r requirements.txt
```

If pip fails with network errors behind a corporate proxy:

```bash
pip install --proxy http://your-proxy:port -r requirements.txt
```

If specific packages fail with corruption errors:

```bash
pip install --force-reinstall --no-cache-dir <package-name>
```

To verify the installation:

```bash
python -c "from air import AsyncAIRefinery; print('airefinery-sdk OK')"
python -c "import fastapi, uvicorn, pandas, pydantic; print('Core packages OK')"
python -c "import fastmcp, httpx, bs4, mcp; print('MCP packages OK')"
```

#### Step 4 — Install Node.js (required for marketing-agents-v2 only)

The marketing-agents-v2 demo uses MCP servers that need `npx` (part of Node.js). Other demos do not require Node.js.

```bash
# Option A: NodeSource (recommended)
curl -fsSL https://deb.nodesource.com/setup_20.x | sudo -E bash -
sudo apt install -y nodejs

# Option B: Ubuntu default (older version, but works)
sudo apt install -y nodejs npm
```

Verify:

```bash
node --version   # Should show v18+ or v20+
npx --version
```

If you cannot install Node.js, all demos except marketing-agents-v2 will still work.

---

## Demos

| Demo | Type | Interface | Description |
|------|------|-----------|-------------|
| **cat-service-diagnostic** | FlowSuperAgent + HumanAgent | CLI / Web UI | Equipment diagnostic with triage routing and technician confirmation |
| **FlowSuperAgent-v2** | FlowSuperAgent | CLI / Web UI | First-match triage routing for support requests |
| **rai-v2** | RAI Guardrails | CLI / Web UI | SearchAgent with 3 responsible AI guardrail rules |
| **salesforce-v2** | SalesforceAgent | CLI / Web UI | Salesforce AgentForce knowledge lookup |
| **EvaluationSuperAgent-v2** | EvaluationSuperAgent | CLI / Web UI | Automated agent quality scoring and comparison |
| **marketing-agents-v2** | FlowSuperAgent + MCP | CLI / Web UI | 6-agent pipeline: research, strategy, report, file save |
| **DeepHumanSelf** | Mixed | CLI only | DeepResearchAgent, HumanAgent, Self-Reflection examples |

---

## Running Demos

### Web UI (most demos)

```bash
cd <demo-directory>
source ../venv/bin/activate
python app_ui.py
# Open http://localhost:8000 in your browser
```

**Exception:** For **marketing-agents-v2**, use `bash start.sh` instead (it starts the MCP servers first).

### CLI

```bash
cd <demo-directory>
source ../venv/bin/activate
python app_cli.py
```

### DeepHumanSelf (nested directories)

```bash
cd "DeepHumanSelf/DeepResearchAgent Examples"
source ../../venv/bin/activate
python example.py

cd "DeepHumanSelf/HumanAgent Examples"
source ../../venv/bin/activate
python example.py demo1   # or demo2, demo3

cd "DeepHumanSelf/Self-Reflection Examples"
source ../../venv/bin/activate
python example.py
```

---

## Example Queries

| Demo | Try This |
|------|----------|
| cat-service-diagnostic | `Fault code E101-3 on a Cat 320, engine misfiring` |
| FlowSuperAgent-v2 | `My internet connection keeps dropping every few minutes` |
| rai-v2 | `What are best practices for team communication?` |
| salesforce-v2 | `Show me the features, benefits, and use cases of Salesforce Agentforce and Data Cloud` |
| EvaluationSuperAgent-v2 | `evaluate` (single) or `compare` (two-agent) |
| marketing-agents-v2 | `Generate a marketing campaign for Agentic AI enterprise adoption` |

---

## Troubleshooting

| Problem | Fix |
|---------|-----|
| `ModuleNotFoundError` | Activate the venv: `source ../venv/bin/activate` |
| `\r': command not found` in shell scripts | Line-ending issue. Run: `git config core.autocrlf input && git checkout .` |
| `apt` errors (403 Forbidden, PPA blocked) | Skip `apt`; use the Python already installed on the system (Step 1 above) |
| `ensurepip is not available` | `sudo apt install -y python3.X-venv` (replace X with your version) |
| `pip install` fails with corruption | `pip install --force-reinstall --no-cache-dir <package>` |
| Port already in use | `fuser -k 8000/tcp` (Linux) or `lsof -ti:8000 \| xargs kill` (macOS) |
| `npx: command not found` | Install Node.js (Step 4 above). Only needed for marketing-agents-v2 |
| Marketing MCP servers fail to start | Ensure ports 4001, 4003, 4004 are free and Node.js is installed |
| Web UI not accessible from Windows host | Access via WSL IP: `hostname -I` then open `http://<ip>:8000` |
| Authentication errors | Verify the `.env` file in the demo directory has a valid `API_KEY` |
