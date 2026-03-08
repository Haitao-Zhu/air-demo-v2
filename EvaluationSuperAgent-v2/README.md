# EvaluationSuperAgent Demo

Demonstrates **EvaluationSuperAgent** for automated agent quality scoring. Evaluates agent responses against predefined metrics, rubrics, and optional ground-truth answers.

## Modes

### Single-Agent Evaluation (`config.yaml`)
Evaluates a `SearchAgent` on 5 metrics (Relevance, Coherence, Accuracy, Conciseness, Source Quality) using 2 sample queries with ground-truth answers.

### Two-Agent Comparison (`config_two_agents.yaml`)
Compares `SearchAgent` vs `PlanningAgent` side-by-side on the same metrics and queries.

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

In the UI:
- Type **"evaluate"** to run single-agent evaluation
- Type **"compare"** to run two-agent comparison

**CLI:**
```bash
python app_cli.py
```

## Notes

- Evaluation takes 1-2 minutes as the system queries each agent and scores responses
- Long JSON results are collapsed in the UI with a "Show more" toggle
