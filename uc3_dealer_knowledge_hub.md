# Use Case 3: Cat Dealer Knowledge Hub

> Complexity: Medium | Duration: 20 min | Key Feature: Orchestrator intelligent routing (multi-agent)

---

## Pain Points Addressed

| Pain Point | Impact | Scale |
|------------|--------|-------|
| **Information silos** | Dealer reps toggle between VisionLink, Parts.cat.com, warranty portals, and spreadsheets to answer a single customer question | 170K+ dealer employees across 2,700 branches |
| **Dealer support variability** | 156 independent dealers at uneven digital maturity; customer experience depends on which dealer they work with | Threatens the $23B -> $28B services revenue target |
| **Fleet management complexity** | Large customers run hundreds of machines across sites; no unified view of hours, service status, and warranty in one place | Missed PM windows cause unplanned downtime costing $1,500-5,000/day per machine |
| **Warranty/CVA confusion** | Dealer reps misinterpret coverage terms, leading to disputed claims, goodwill write-offs, and delayed repairs | CVAs are a major revenue driver; mismanagement erodes margins |

## Synthetic Data

**`data/fleet.csv`** -- Customer fleet registry (~200 rows)

| Column | Type | Example | Notes |
|--------|------|---------|-------|
| customer_id | str | `CUST-4521` | Unique account identifier |
| customer_name | str | `Turner Construction` | Company name |
| machine_serial | str | `CAT0320GC-7841` | Unique serial per machine |
| model | str | `Cat 320 GC` | Equipment model |
| year_manufactured | int | `2022` | Production year |
| hours_operated | int | `4850` | Total engine hours from telematics |
| location | str | `Phoenix, AZ` | Current job site |
| last_service_date | date | `2026-01-15` | Most recent completed service |
| next_service_due | date | `2026-04-15` | Calculated next PM date |
| service_interval_hours | int | `500` | Hours between scheduled services |
| warranty_expiry | date | `2027-06-30` | Warranty end date |
| warranty_type | str | `Full Machine` | Full Machine / Powertrain / Extended |
| cva_tier | str | `CVA-Premium` | None / CVA-Preventive / CVA-Premium / CVA-Gold |
| status | str | `Active` | Active / Idle / In-Shop / Decommissioned |

**`data/maintenance_schedule.csv`** -- Standard maintenance intervals (~80 rows)

| Column | Type | Example | Notes |
|--------|------|---------|-------|
| model | str | `Cat 320 GC` | FK to fleet.csv model |
| interval_hours | int | `500` | Service trigger point |
| service_type | str | `PM2 - Intermediate` | PM1 / PM2 / PM3 / PM4 |
| tasks | str | `Engine oil, hydraulic filter, air filter` | Comma-separated task list |
| estimated_hours | float | `3.0` | Labor hours |
| required_parts | str | `1R-0751, 5I-8670, 131-8822` | Cat part numbers |
| estimated_cost | float | `850.00` | Parts + labor USD |

## Architecture

```
                         +---------------------------+
                         |      ORCHESTRATOR         |
                         |  enable_routing: true     |
                         |  decompose: true          |
                         +---------------------------+
                           /     |       |        \
                          /      |       |         \
              +-----------+ +----------+ +--------+ +-----------+
              | Analytics | | Warranty | | Search | | Planning  |
              | Agent     | | Policy   | | Agent  | | Agent     |
              | (fleet +  | | Agent    | |        | |           |
              |  maint    | | (Utility)| |(Search)| | (Planning)|
              |  CSVs)    | |          | |        | |           |
              +-----------+ +----------+ +--------+ +-----------+
                   |              |           |            |
              fleet.csv      magic_prompt  Google     Structured
              maint.csv      with CVA/     Search     maintenance
                             warranty                  plans
                             policy KB
```

## Agents Used

| Agent | Class | Purpose | Why This Agent |
|-------|-------|---------|----------------|
| Fleet Analytics | **AnalyticsAgent** | Queries fleet.csv and maintenance_schedule.csv with natural language; filtering, aggregation, joins, visualization | Generates Pandas code from NL -- no CustomAgent needed for data lookups |
| Warranty Policy Advisor | **UtilityAgent** | Interprets warranty terms, CVA coverage, claim eligibility | magic_prompt embeds domain policy knowledge; answers without external calls |
| Cat Equipment Search | **SearchAgent** | General Cat equipment specs, comparisons, application guidance | Zero-code web search; YAML-only config |
| Service Planner | **PlanningAgent** | Generates multi-step maintenance plans from fleet state | Produces structured plans with timelines and resource allocation |

**Key design decision:** AnalyticsAgent with PandasExecutor replaces the two CustomAgents from the prior design. It converts natural-language questions into Pandas operations, executes them against the CSVs, and returns tabular or visual results -- all without writing Python handler code.

**decompose: true** allows the orchestrator to break complex dealer queries (e.g., "Which Turner machines are overdue for service AND have expiring warranty?") into subtasks routed to different agents, then synthesize a unified answer.

## YAML Configuration

```yaml
orchestrator:
  agent_list:
    - agent_name: "Fleet Analytics"
    - agent_name: "Warranty Policy Advisor"
    - agent_name: "Cat Equipment Search"
    - agent_name: "Service Planner"
  enable_routing: true
  decompose: true
  contexts:
    - date
    - chat_history
  system_prompt_suffix: |
    You are the Cat Dealer Knowledge Hub. Route each query to the most
    appropriate specialist agent. For multi-part questions, decompose into
    subtasks. Always include machine serial numbers and customer IDs when
    referencing specific assets.

utility_agents:
  - agent_class: AnalyticsAgent
    agent_name: "Fleet Analytics"
    agent_description: |
      Answers data questions about customer fleets: machine inventory, hours
      operated, service history, upcoming maintenance, warranty dates, CVA
      tiers, and fleet-level aggregations. Handles filtering, sorting,
      grouping, cross-referencing fleet with maintenance schedules, and
      generating charts. Use for ANY question requiring data lookup or
      calculation from fleet or maintenance records.
    config:
      executor:
        type: PandasExecutor
        tables:
          - name: fleet
            file_path: data/fleet.csv
            description: "Customer fleet registry with machine details, hours, warranty, CVA status"
          - name: maintenance
            file_path: data/maintenance_schedule.csv
            description: "Standard maintenance intervals, tasks, parts, and costs by model"
      api:
        - PandasAPI

  - agent_class: UtilityAgent
    agent_name: "Warranty Policy Advisor"
    agent_description: |
      Interprets Cat warranty terms, Customer Value Agreement (CVA) coverage
      tiers, claim eligibility, and coverage exclusions. Use for policy
      questions like "Does CVA-Premium cover hydraulic pump replacement?" or
      "What is excluded from Powertrain warranty?"
    config:
      magic_prompt: |
        You are a Cat warranty and CVA policy expert. Answer based on these rules:

        WARRANTY TYPES:
        - Full Machine: covers all components for 2 years / 3,000 hours
        - Powertrain: engine, transmission, final drives for 3 years / 5,000 hours
        - Extended: adds 1 year / 2,000 hours to base coverage

        CVA TIERS:
        - CVA-Preventive: scheduled PMs only
        - CVA-Premium: PMs + wear parts + S-O-S fluid analysis
        - CVA-Gold: full-coverage including repair, ground-engaging tools, undercarriage

        EXCLUSIONS: operator abuse, unauthorized modifications, non-Cat fluids.

        Question: {query}

  - agent_class: SearchAgent
    agent_name: "Cat Equipment Search"
    agent_description: |
      Searches the web for Cat equipment specifications, model comparisons,
      application best practices, and general product information. Use for
      questions not answerable from fleet data or warranty policy.

  - agent_class: PlanningAgent
    agent_name: "Service Planner"
    agent_description: |
      Creates structured maintenance plans, service schedules, and resource
      allocation timelines. Use when a dealer needs a multi-step plan for
      upcoming services, shop scheduling, or seasonal fleet prep.
```

## Agent Routing Flow

```
User Query
    |
    v
ORCHESTRATOR evaluates agent_description fields
    |
    +-- Data question? (hours, machines, costs, counts) --> Fleet Analytics
    |
    +-- Policy question? (warranty, CVA, coverage)       --> Warranty Policy Advisor
    |
    +-- Product/spec question? (models, comparisons)     --> Cat Equipment Search
    |
    +-- Planning request? (schedule, prep, timeline)     --> Service Planner
    |
    +-- Multi-part question? (decompose=true)
         --> Split into subtasks, route each independently, merge results
```

## Process Flow -- Three Example Queries

**Query 1 -- Fleet data (routes to Fleet Analytics):**
```
Dealer: "Which Turner Construction machines are past 4,000 hours and due for service this month?"

  Orchestrator --> Fleet Analytics (data filtering + date logic)
    --> Pandas: fleet[(fleet.customer_name=='Turner Construction')
                      & (fleet.hours_operated > 4000)
                      & (fleet.next_service_due <= '2026-03-31')]
    --> Returns: 3 machines with serial, model, hours, next service date, estimated cost
```

**Query 2 -- Warranty policy (routes to Warranty Policy Advisor):**
```
Dealer: "Does CVA-Premium cover hydraulic pump replacement on a Cat 320 GC?"

  Orchestrator --> Warranty Policy Advisor (policy interpretation)
    --> magic_prompt injects CVA rules + query
    --> Returns: Yes, CVA-Premium includes wear parts; hydraulic pump
        is covered if failure is not due to operator abuse or non-Cat fluids.
```

**Query 3 -- Decomposed multi-part (routes to two agents):**
```
Dealer: "List all machines with warranty expiring in 90 days and recommend a CVA upgrade plan."

  Orchestrator decomposes:
    Subtask 1 --> Fleet Analytics: filter warranty_expiry within 90 days of today
    Subtask 2 --> Service Planner: generate CVA upgrade recommendations per machine
  Orchestrator merges: table of at-risk machines + per-machine upgrade plan with cost/benefit
```

## AI Refinery Value Demonstrated

| Capability | What It Proves |
|------------|---------------|
| **Intelligent routing** | Orchestrator acts as a traffic cop -- zero routing code, just agent_description matching |
| **AnalyticsAgent over CustomAgent** | Natural language to Pandas eliminates custom Python for every data query; new CSVs = new tables, not new code |
| **UtilityAgent as policy engine** | Domain knowledge embedded in magic_prompt; no retrieval pipeline needed for structured policy |
| **decompose=true** | Complex dealer questions auto-split across specialists and re-merged -- mirrors real dealer workflows |
| **Uniform dealer experience** | Same Knowledge Hub for all 156 dealers; levels the playing field regardless of dealer IT maturity |
| **Services revenue enablement** | Proactive warranty/CVA visibility supports the $23B to $28B services growth target |
