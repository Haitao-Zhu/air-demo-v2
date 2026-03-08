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

- "What is our return policy?"
- "How do I reset my password?"
- "What are the business hours for support?"
