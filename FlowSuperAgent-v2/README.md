# FlowSuperAgent Demo

Demonstrates **FlowSuperAgent** with deterministic first-match triage routing. A support request is classified as technical or billing, then routed to the appropriate handler, and finally summarized.

## Architecture

```
User Query
    |
Support Classifier (first-match triage)
    |-- "technical" --> Technical Troubleshooter --> Final Support Summary
    |-- "billing"   --> Billing Assistant        --> Final Support Summary
    |-- default     --> Both agents              --> Final Support Summary
```

All agents are `PlanningAgent` (server-side, no external dependencies).

## Setup

```bash
# From this directory
source venv/bin/activate

# Register the project (happens automatically on first run)
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

- "My internet connection keeps dropping every few minutes"
- "I was charged twice on my last invoice"
- "I can't log in and I also need to update my billing address"
