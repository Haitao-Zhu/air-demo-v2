# Salesforce AgentForce Demo

Demonstrates **SalesforceAgent** integration with Salesforce AgentForce. Queries are routed to a Salesforce knowledge agent that can look up articles, policies, and support information.

## Prerequisites

Requires valid Salesforce credentials in `.env`:
- `SALESFORCE_CLIENT_KEY`
- `SALESFORCE_CLIENT_SECRET`
- Salesforce domain and agent ID are configured in `config.yaml`

## Setup

```bash
source venv/bin/activate
python -c "from auth import *"
```

## Run

**Web UI:**
```bash
python app_ui.py
# Open http://localhost:8000
```

**CLI:**
```bash
python app_cli.py
```

## Example Prompts

- "Show me the features, benefits, and use cases of Salesforce Agentforce and Data Cloud"
- "How do AgentForce and Data Cloud work together to enhance CRM processes?"
- "Show me the features related to AI-powered customer interactions"
