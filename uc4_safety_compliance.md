# Use Case 4: Cat Safety & Compliance Advisor

> Complexity: High | Duration: 20 min | Key Feature: 4 built-in agent types, zero CustomAgent code

---

## Pain Points Addressed

Construction and mining rank among the deadliest industries. OSHA reports roughly 1,000 fatalities per year in construction alone; MSHA tracks hundreds more in mining. Caterpillar, whose equipment operates on virtually every major jobsite worldwide, holds safety as its number-one value.

- **Regulatory complexity**: OSHA (29 CFR 1926), MSHA (30 CFR Parts 46-90), EPA, plus state and local regulations vary by jurisdiction. A single jobsite may fall under overlapping federal and state authority.
- **Incident documentation gaps**: Post-incident reports are often incomplete or inconsistent, delaying root-cause analysis and corrective action.
- **Training and awareness**: High crew turnover means constant re-education. Supervisors need daily toolbox talks tailored to current equipment and conditions.
- **Trend blindness**: Without analytics, recurring near-miss patterns go unnoticed until a serious injury occurs.
- **Existing Cat technology**: Cat DSS (Driver Safety System) detects fatigue and distraction; Cat Command enables remote operation in hazardous zones. This advisor complements those systems at the procedural and regulatory layer.

## Synthetic Data

### `data/safety_protocols.csv`

| Column | Type | Example |
|--------|------|---------|
| protocol_id | string | `SP-0042` |
| category | string | `Excavator Operations` |
| applicable_models | string | `Cat 320, Cat 325, Cat 330` |
| hazard | string | `Struck-by: swing radius contact` |
| risk_level | enum | `High` / `Medium` / `Low` |
| pre_operation_checks | string | `Walk-around inspection; mirror check; horn test` |
| operating_procedure | string | `Establish swing zone; use spotter for blind spots` |
| ppe_required | string | `Hard hat, high-vis vest, steel-toe boots, safety glasses` |
| emergency_procedure | string | `Stop machine; lower bucket; shut off engine; call 911` |
| regulatory_ref | string | `OSHA 1926.1428, MSHA 30 CFR 56` |

### `data/incident_log.csv`

| Column | Type | Example |
|--------|------|---------|
| incident_id | string | `INC-2026-0158` |
| date | date | `2026-02-10` |
| site | string | `Phoenix I-17 Highway Expansion` |
| machine_model | string | `Cat 320 GC` |
| incident_type | string | `Near Miss - Swing Radius` |
| severity | enum | `Critical` / `High` / `Medium` / `Low` |
| description | string | `Excavator swing contacted material pile near worker path` |
| root_cause | string | `Spotter not in position; operator blind spot` |
| corrective_action | string | `Re-briefed swing zone protocol; added physical barrier` |
| injuries | int | `0` |
| lost_work_days | int | `0` |

## Agents Used

This use case showcases **four distinct built-in agent types** with zero CustomAgent code -- the broadest agent diversity of any demo use case.

| Agent | Class | Role |
|-------|-------|------|
| Safety Protocol Advisor | UtilityAgent | Domain-specific safety protocol Q&A via magic_prompt |
| Incident Analyst | AnalyticsAgent | Pandas-based analysis of incident_log.csv and safety_protocols.csv |
| Regulation Searcher | SearchAgent | Live web search for current OSHA/MSHA/EPA regulations |
| Safety Doc Writer | AuthorAgent | Generates structured toolbox talks, safety briefings, incident reports |
| Incident Report Flow | FlowSuperAgent | Orchestrates multi-step incident reporting workflow |

## Architecture

```
Orchestrator (enable_routing: true, decompose: true)
  |
  |-- Safety Protocol Advisor (UtilityAgent)
  |     magic_prompt: Cat equipment safety domain knowledge
  |
  |-- Incident Analyst (AnalyticsAgent)
  |     PandasExecutor on: incident_log.csv, safety_protocols.csv
  |
  |-- Regulation Searcher (SearchAgent)
  |     Google search for OSHA / MSHA / EPA regulations
  |
  |-- Safety Doc Writer (AuthorAgent)
  |     leading_questions drive structured safety documents
  |
  |-- Incident Report Flow (FlowSuperAgent)
  |     DAG: HumanAgent --> AnalyticsAgent --> AuthorAgent --> SearchAgent
  |           collect        find similar      generate        cite
  |           details        past incidents    report          regulations
```

## YAML Configuration

```yaml
orchestrator:
  agent_list:
    - agent_name: "Safety Protocol Advisor"
    - agent_name: "Incident Analyst"
    - agent_name: "Regulation Searcher"
    - agent_name: "Safety Doc Writer"
    - agent_name: "Incident Report Flow"
  decompose: true
  contexts:
    - date

utility_agents:
  - agent_class: UtilityAgent
    agent_name: "Safety Protocol Advisor"
    agent_description: >
      Answers questions about Caterpillar equipment safety protocols, PPE
      requirements, pre-operation checklists, emergency procedures, and
      hazard identification for construction and mining operations.
    config:
      magic_prompt: >
        You are a Caterpillar safety expert. You know Cat equipment models,
        their hazards, required PPE, pre-operation inspection steps, safe
        operating procedures, and emergency shutdown protocols. Always
        reference the applicable OSHA or MSHA regulation codes. Emphasize
        that safety is non-negotiable. If unsure, direct the user to their
        site safety manager.

  - agent_class: AnalyticsAgent
    agent_name: "Incident Analyst"
    agent_description: >
      Analyzes safety incident data to find trends, top causes, severity
      breakdowns by site or equipment model, and time-based patterns. Also
      queries safety protocol data for coverage gaps.
    config:
      executor: PandasExecutor
      tables:
        - name: incident_log
          path: data/incident_log.csv
          description: >
            Historical safety incidents with columns: incident_id, date,
            site, machine_model, incident_type, severity, description,
            root_cause, corrective_action, injuries, lost_work_days
        - name: safety_protocols
          path: data/safety_protocols.csv
          description: >
            Equipment safety protocols with columns: protocol_id, category,
            applicable_models, hazard, risk_level, pre_operation_checks,
            operating_procedure, ppe_required, emergency_procedure,
            regulatory_ref

  - agent_class: SearchAgent
    agent_name: "Regulation Searcher"
    agent_description: >
      Searches the web for the latest OSHA, MSHA, and EPA safety regulations,
      compliance deadlines, enforcement actions, and industry best practices
      for construction and mining operations.

  - agent_class: AuthorAgent
    agent_name: "Safety Doc Writer"
    agent_description: >
      Generates structured safety documents including toolbox talks, daily
      safety briefings, incident summary reports, and safety improvement
      plans with consistent formatting.
    config:
      leading_questions:
        - "What specific equipment or operation does this document cover?"
        - "What is the target audience (operators, supervisors, new hires)?"
        - "Are there recent incidents or hazards to highlight?"
        - "Which regulatory standards should be referenced?"

  - agent_class: FlowSuperAgent
    agent_name: "Incident Report Flow"
    agent_description: >
      Runs the full incident reporting workflow: collects incident details
      from the user, finds similar past incidents, generates a structured
      report, and cites applicable regulations. Use when someone says
      'report an incident' or 'file a safety event'.
    config:
      flow:
        - agent_name: "Detail Collector"
          agent_class: HumanAgent
          prompt: >
            Collect: date, site, equipment, description, injuries, and
            immediate actions taken.
        - agent_name: "Similar Incident Lookup"
          agent_class: AnalyticsAgent
          prompt: >
            Search incident_log for past incidents with matching equipment
            or incident type. Return top 3 similar events.
        - agent_name: "Report Generator"
          agent_class: AuthorAgent
          prompt: >
            Produce a formal incident report with sections: Summary,
            Equipment Involved, Timeline, Root Cause Analysis, Similar
            Past Incidents, Corrective Actions, Regulatory References.
        - agent_name: "Regulation Lookup"
          agent_class: SearchAgent
          prompt: >
            Search for OSHA/MSHA regulations applicable to this incident
            type. Append citations to the report.
```

## Agent Flow and Routing

The orchestrator routes based on `agent_description` matching:

- **Protocol/PPE/procedure questions** --> Safety Protocol Advisor (UtilityAgent)
- **Data queries** ("trends", "how many", "top causes", "breakdown") --> Incident Analyst (AnalyticsAgent)
- **Regulation lookups** ("OSHA", "MSHA", "EPA", "compliance") --> Regulation Searcher (SearchAgent)
- **Document generation** ("toolbox talk", "safety briefing", "write a...") --> Safety Doc Writer (AuthorAgent)
- **Incident reporting** ("report an incident", "file a safety event") --> Incident Report Flow (FlowSuperAgent)

With `decompose: true`, complex queries like "What are our top incident types this quarter and what OSHA regulations apply to each?" split into subtasks: AnalyticsAgent retrieves the data, then SearchAgent looks up the regulations.

## Process Flow -- Three Example Queries

**Query 1: Protocol lookup (UtilityAgent)**
```
User: "What PPE is required for operating a Cat 390F excavator near a highway?"
  --> Orchestrator routes to Safety Protocol Advisor
    --> magic_prompt provides domain expertise
    --> Response: hard hat, high-vis class 3 vest, steel-toe boots, safety glasses,
        hearing protection, plus highway-specific traffic control PPE per OSHA 1926.651
```

**Query 2: Trend analysis (AnalyticsAgent)**
```
User: "Show me the top 5 incident types across all sites this quarter with severity breakdown"
  --> Orchestrator routes to Incident Analyst
    --> PandasExecutor runs: group by incident_type, filter date >= Q1 2026,
        pivot on severity, sort by count descending, limit 5
    --> Response: table with incident types, counts, severity distribution, trend arrows
```

**Query 3: Full incident report (FlowSuperAgent DAG)**
```
User: "I need to report a safety incident"
  --> Orchestrator routes to Incident Report Flow
    --> Step 1 (HumanAgent): Asks user for date, site, equipment, description, injuries
    --> Step 2 (AnalyticsAgent): Finds 3 similar past incidents from incident_log.csv
    --> Step 3 (AuthorAgent): Generates formal report with all sections
    --> Step 4 (SearchAgent): Appends applicable OSHA/MSHA regulation citations
    --> Final output: Complete, structured incident report ready for filing
```

## AI Refinery Value Demonstrated

- **Agent breadth**: Four distinct built-in agent types (UtilityAgent, AnalyticsAgent, SearchAgent, AuthorAgent) plus FlowSuperAgent -- all configured via YAML with zero custom Python code.
- **Domain specialization without code**: The `magic_prompt` on UtilityAgent and `leading_questions` on AuthorAgent inject Cat safety expertise purely through configuration.
- **Structured content generation**: AuthorAgent produces consistent, auditable safety documents that meet regulatory documentation standards.
- **Live regulation access**: SearchAgent ensures advice reflects the latest regulatory updates, not stale training data.
- **Deterministic workflows**: FlowSuperAgent chains agents into a repeatable incident reporting pipeline, critical for compliance audit trails.
- **Life-safety impact**: This is not a productivity tool -- it directly reduces risk in industries where mistakes cost lives.
