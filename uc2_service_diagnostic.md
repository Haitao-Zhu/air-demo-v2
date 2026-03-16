# Use Case 2: Cat Service Diagnostic Flow

> Complexity: Advanced | Duration: 25 min | Hero Feature: FlowSuperAgent (deterministic DAG with triage)

---

## 1. Pain Points Addressed

| Problem | Impact | Numbers |
|---------|--------|---------|
| Unplanned downtime | Mining trucks idle while techs diagnose | $10K-$50K/hr lost revenue |
| Low first-time fix rates | Wrong diagnosis or missing parts force return visits | ~30% of service calls need a second trip |
| Technician skill shortage | Rising avg age, hard to recruit skilled diesel/hydraulic techs | 170K+ dealer employees across 156 dealers, 2700 branches |
| Manual lookup burden | Thousands of fault codes, TSBs, service manuals | 30-60 min per diagnostic lookup |
| Parts ordering errors | Incomplete diagnosis leads to wrong parts | Delays add 1-3 days to repair |
| Inconsistent service quality | Expert knowledge trapped in senior techs' heads | Varies across 156 dealers |

Business target: grow services revenue from $23B to $28B. Improving first-time fix rates across 1.6M connected machines is the lever.

## 2. Synthetic Data

### `data/fault_codes.csv` (50 rows)

| Column | Type | Example |
|--------|------|---------|
| fault_code | str | `E361-2` |
| severity | str | `Critical` / `Warning` / `Info` |
| system | str | `Engine` / `Hydraulic` / `Electrical` / `Transmission` |
| component | str | `Fuel Injector #3` |
| description | str | `Fuel injector circuit malfunction` |
| machine_model | str | `Cat 320` |
| possible_causes | str | `Wiring harness damage; Injector failure; ECM fault` |
| diagnostic_steps | str | `1. Check wiring harness 2. Measure resistance 3. Swap injector` |
| estimated_repair_hrs | float | `2.5` |
| required_parts | str | `457-5765, 523-1893` |
| tech_level | int | `2` (1=basic, 2=intermediate, 3=specialist) |

### `data/parts_inventory.csv` (80 rows)

| Column | Type | Example |
|--------|------|---------|
| part_number | str | `457-5765` |
| part_name | str | `Fuel Injector Assembly` |
| category | str | `Engine - Fuel System` |
| unit_price | float | `1245.00` |
| dealer_stock | int | `3` |
| warehouse_stock | int | `15` |
| lead_time_days | int | `0` |
| compatible_models | str | `Cat 320, Cat 325, Cat 330` |
| superseded_by | str | `null` |

## 3. Agents Used

| Agent | Class | Why This Class | Role |
|-------|-------|----------------|------|
| Fault Lookup Agent | **AnalyticsAgent** | CSV query via natural language -- no Python needed | Query fault_codes.csv by fault code and machine model |
| Severity Router | (triage node) | Built-in FlowSuperAgent triage | Route Critical faults to human confirmation, others straight through |
| Tech Confirmation | **HumanAgent** | Critical faults need tech sign-off before parts ordering | Ask technician to confirm symptoms match diagnosis |
| Parts Lookup Agent | **AnalyticsAgent** | CSV query via natural language -- no Python needed | Query parts_inventory.csv for availability and pricing |
| Report Generator | **AuthorAgent** | Compiles structured output from shared memory -- no Python needed | Generate formatted service report from upstream agent outputs |
| Cat Service Flow | **FlowSuperAgent** | Deterministic DAG with triage and conditional routing | Orchestrate the full diagnostic pipeline |

**CustomAgent count: 0.** Every agent uses a built-in class.

## 4. Architecture Diagram

```
                        Cat Service Flow (FlowSuperAgent)
                        =================================

  Technician Query
        |
        v
  +------------------+
  | Fault Lookup     |  AnalyticsAgent (PandasExecutor on fault_codes.csv)
  | Agent            |
  +------------------+
        |
        v
  +------------------+      severity == "Critical"       +------------------+
  | Severity Router  | ----------------------------------> | Tech Confirmation|
  | (triage node)    |                                    | (HumanAgent)     |
  +------------------+                                    +------------------+
        | default (Warning/Info)                                  |
        +---------------------------+-----------------------------+
                                    |
                                    v
                            +------------------+
                            | Parts Lookup     |  AnalyticsAgent (PandasExecutor on parts_inventory.csv)
                            | Agent            |
                            +------------------+
                                    |
                                    v
                            +------------------+
                            | Report Generator |  AuthorAgent (compiles from memory)
                            +------------------+
                                    |
                                    v
                            Service Report Output
```

## 5. YAML Configuration

```yaml
orchestrator:
  agent_list:
    - agent_name: "Cat Service Flow"
  decompose: false

super_agents:
  - agent_class: FlowSuperAgent
    agent_name: "Cat Service Flow"
    agent_description: >
      Diagnoses equipment faults end-to-end. Accepts a fault code and machine model,
      looks up diagnosis, checks parts, and generates a service report.
      Invoke when a technician reports a fault code or equipment issue.
    config:
      goal: "Diagnose equipment fault, check parts availability, and generate a complete service report"
      agent_list:
        - agent_name: "Fault Lookup Agent"
          next_step:
            - step_name: "Tech Confirmation"
              condition: "severity is Critical"
            - step_name: "Parts Lookup Agent"
              default: true
        - agent_name: "Tech Confirmation"
          next_step:
            - "Parts Lookup Agent"
        - agent_name: "Parts Lookup Agent"
          next_step:
            - "Report Generator"
        - agent_name: "Report Generator"

utility_agents:
  - agent_class: AnalyticsAgent
    agent_name: "Fault Lookup Agent"
    agent_description: >
      Looks up fault codes in the Cat diagnostic database. Returns severity, root causes,
      diagnostic steps, required parts, and estimated repair time.
    config:
      executor_config:
        executor_name: PandasExecutor
        tables:
          - table_name: fault_codes
            table_path: data/fault_codes.csv
            table_description: >
              Caterpillar equipment fault code database with severity, causes,
              diagnostic steps, required parts, and repair time estimates.

  - agent_class: AnalyticsAgent
    agent_name: "Parts Lookup Agent"
    agent_description: >
      Checks parts availability and pricing. Uses required_parts from the fault lookup
      to query dealer and warehouse inventory, lead times, and compatible models.
    config:
      executor_config:
        executor_name: PandasExecutor
        tables:
          - table_name: parts_inventory
            table_path: data/parts_inventory.csv
            table_description: >
              Dealer and warehouse parts inventory with stock levels, pricing,
              lead times, and model compatibility.

  - agent_class: HumanAgent
    agent_name: "Tech Confirmation"
    agent_description: >
      For Critical-severity faults, asks the technician to confirm symptoms match
      the diagnosis before proceeding to parts ordering.
    config:
      leading_questions:
        - "Does the diagnosed fault match the symptoms you are observing on the machine?"
        - "Are there any additional fault codes or symptoms not yet reported?"

  - agent_class: AuthorAgent
    agent_name: "Report Generator"
    agent_description: >
      Compiles a formatted service report including diagnosis, parts list with
      availability, step-by-step repair procedure, and estimated time/cost.
    config:
      leading_questions:
        - "Machine model and fault code"
        - "Severity and root cause analysis"
        - "Step-by-step repair procedure"
        - "Parts required with availability and pricing"
        - "Estimated repair time and technician level required"
      memory_attribute_key: "chat_history"
```

## 6. Agent Flow -- Data Passing

1. **Technician query** enters the FlowSuperAgent as the initial prompt.
2. **Fault Lookup Agent** receives the query, generates a Pandas command like `fault_codes[fault_codes['fault_code'] == 'E361-2']`, and returns structured diagnosis. Output is written to shared `chat_history`.
3. **Triage node** inspects Fault Lookup output. If severity == "Critical", routes to Tech Confirmation; otherwise skips to Parts Lookup.
4. **Tech Confirmation** (HumanAgent) presents the diagnosis and asks the technician to confirm. Response appended to `chat_history`.
5. **Parts Lookup Agent** reads `chat_history` to extract `required_parts`, generates Pandas query like `parts_inventory[parts_inventory['part_number'].isin(['457-5765','523-1893'])]`, returns availability. Appended to `chat_history`.
6. **Report Generator** (AuthorAgent) reads full `chat_history` via `memory_attribute_key` and compiles the final structured service report.

## 7. Process Flow -- Example Queries

### Query 1: "Fault code E361-2 on Cat 320, engine running rough"

| Step | Agent | Action | Output |
|------|-------|--------|--------|
| 1 | Fault Lookup | `fault_codes[fault_codes['fault_code']=='E361-2']` | Severity: **Critical**. Fuel Injector #3 circuit malfunction. Causes: wiring harness, injector failure, ECM fault. 5-step procedure. Parts: 457-5765, 523-1893. Est: 2.5 hrs. |
| 2 | Triage | Severity == Critical | Routes to Tech Confirmation |
| 3 | Tech Confirmation | "Does diagnosed fault match symptoms?" | Tech confirms: "Yes, cylinder 3 misfire confirmed" |
| 4 | Parts Lookup | `parts_inventory[parts_inventory['part_number'].isin(['457-5765','523-1893'])]` | Injector: 3 in stock, $1,245. Harness: 1 in stock, $387. Total: $1,632 |
| 5 | Report Generator | Compile from chat_history | Full service report (see below) |

**Final output excerpt:** Machine: Cat 320 | Fault: E361-2 CRITICAL | Root Cause: Fuel Injector #3 Circuit | Repair: 5 steps, 2.5 hrs, Level 2 tech | Parts: $1,632 total, all in stock.

### Query 2: "Cat 950M showing H340-3 warning, hydraulic temp high"

| Step | Agent | Action | Output |
|------|-------|--------|--------|
| 1 | Fault Lookup | `fault_codes[fault_codes['fault_code']=='H340-3']` | Severity: **Warning**. Hydraulic oil overtemp. Causes: low oil, clogged cooler, pump wear. 3-step procedure. Parts: 289-1044. Est: 1.0 hr. |
| 2 | Triage | Severity == Warning | Skips to Parts Lookup (no human confirmation needed) |
| 3 | Parts Lookup | `parts_inventory[parts_inventory['part_number']=='289-1044']` | Hydraulic filter: 8 in stock, $142. |
| 4 | Report Generator | Compile from chat_history | Full service report |

**Key difference:** Warning-level faults skip the human confirmation step -- faster turnaround for routine issues.

## 8. Python Registration (executor_dict)

```python
from ai_refinery.agent_executor import PandasAPI

executor_dict = {
    "Fault Lookup Agent": PandasAPI,
    "Parts Lookup Agent": PandasAPI,
}
```

No custom async functions needed. Both AnalyticsAgents use the built-in PandasAPI executor.

## 9. AI Refinery Value -- Why FlowSuperAgent?

| Capability | FlowSuperAgent | Manual API Chaining |
|------------|---------------|---------------------|
| Deterministic execution order | DAG defined in YAML -- guaranteed sequence | Must code ordering logic manually |
| Conditional routing (triage) | Built-in `condition`/`default` on edges | Custom if/else branching code |
| Human-in-the-loop | Drop in HumanAgent at any node | Build custom UI + wait logic |
| Shared memory | Automatic chat_history propagation | Manual context passing between calls |
| Reconfiguration | Edit YAML, no code changes | Redeploy code for any flow change |
| Auditability | Each agent's output is a traceable node | Logs scattered across services |

**Bottom line:** The entire diagnostic pipeline -- CSV lookups, severity-based routing, human confirmation, and report generation -- is built with **zero CustomAgent code**. A solutions architect can redesign the flow by editing YAML alone. This is the strongest possible demo of AI Refinery's value: enterprise-grade agent orchestration without bespoke Python for every step.
