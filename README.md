# AI Refinery Demo Collection

A collection of demo applications built on the **AI Refinery SDK**, showcasing agentic AI patterns including multi-agent orchestration, conditional routing, human-in-the-loop, RAI guardrails, MCP integration, and more.

---

## Environment Setup (Windows WSL)

### 1. Install system dependencies

```bash
sudo apt update && sudo apt install -y python3 python3-pip python3-venv git curl
```

For **marketing-agents-v2** only — install Node.js:

```bash
curl -fsSL https://deb.nodesource.com/setup_20.x | sudo -E bash -
sudo apt install -y nodejs
```

### 2. Clone the repo

```bash
git clone https://github.com/Haitao-Zhu/air-demo-v2.git
cd air-demo-v2
```

### 3. Create the universal virtual environment

```bash
python3 -m venv venv
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
```

### 4. Ready to go

All credentials (API keys, Salesforce keys) are pre-configured in each demo's `.env` file and source code. No additional setup needed.

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
| salesforce-v2 | `What is our return policy?` |
| EvaluationSuperAgent-v2 | `evaluate` (single) or `compare` (two-agent) |
| marketing-agents-v2 | `Generate a marketing campaign for Agentic AI enterprise adoption` |

---

## Troubleshooting

- **`ModuleNotFoundError`**: Make sure the venv is activated — `source ../venv/bin/activate` (or `../../venv/bin/activate` for DeepHumanSelf sub-demos)
- **Authentication errors**: Verify your `.env` file has a valid `API_KEY`
- **Port already in use**: Kill the process on the port (e.g. `lsof -ti:8000 | xargs kill`) then retry
- **marketing-agents-v2 MCP servers fail**: Ensure Node.js is installed and ports 4001, 4003, 4004, 8000 are free
- **Web UI not accessible from Windows host**: Use `python app_ui.py --host 0.0.0.0` or access via the WSL IP address
