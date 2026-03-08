# AI Refinery Demo Collection

All demos share a single Python virtual environment at `../venv/`. Each demo directory has a `venv` symlink pointing to it.

## Quick Start

```bash
# Activate the shared venv (from any demo directory)
source venv/bin/activate
```

## Demos

| Demo | Type | Interface | Description |
|------|------|-----------|-------------|
| **cat-service-diagnostic** | FlowSuperAgent + HumanAgent | CLI / Web UI | Equipment diagnostic with triage routing and technician confirmation |
| **FlowSuperAgent-v2** | FlowSuperAgent | Web UI | First-match triage routing for support requests |
| **rai-v2** | RAI Guardrails | Web UI | SearchAgent with 3 responsible AI guardrail rules |
| **salesforce-v2** | SalesforceAgent | Web UI | Salesforce AgentForce knowledge lookup |
| **EvaluationSuperAgent-v2** | EvaluationSuperAgent | Web UI | Automated agent quality scoring and comparison |
| **marketing-agents-v2** | FlowSuperAgent + MCP | Web UI | 6-agent pipeline: research, strategy, report, file save |
| **DeepHumanSelf** | Mixed | CLI only | DeepResearchAgent, HumanAgent, Self-Reflection examples |

## Running Web UI Demos

```bash
cd <demo-directory>
source venv/bin/activate
python app_ui.py
# Open http://localhost:8000
```

Exception: **marketing-agents-v2** — use `bash start.sh` (starts MCP servers first).

## Running CLI Demos

```bash
cd <demo-directory>
source venv/bin/activate
python app_cli.py
```

## Shared Environment

All demos use the same venv with these key packages:
- `airefinery-sdk` — AI Refinery SDK (`AsyncAIRefinery` + legacy `DistillerClient`)
- `fastapi` + `uvicorn` — Web UI server
- `fastmcp`, `mcp`, `mcp-proxy` — MCP server support
- `python-dotenv` — Environment variable loading

## Credentials

Web UI demos load credentials from `.env` in each demo directory. DeepHumanSelf uses environment variables directly:

```bash
export API_KEY="<your-key>"
export AIREFINERY_ADDRESS="https://api.airefinery.accenture.com"
```
