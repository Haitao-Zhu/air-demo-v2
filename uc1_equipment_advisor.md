# Use Case 1: Cat Equipment Advisor

> Complexity: Medium | Duration: 30 min | Agents: 4 | Key Feature: Multi-agent orchestration with zero custom code

---

## 1. Pain Points Addressed

| Problem | Who It Hurts | Scale / Impact |
|---------|-------------|----------------|
| Sales reps manually search specs across 300+ machine models per inquiry | 156 dealers, 2700 branches | Avg 45 min per equipment recommendation; ~$2.1B in annual dealer labor costs |
| Inconsistent equipment recommendations from junior vs senior reps | Customers, dealers | 38% of new reps cite product complexity as top barrier; leads to mis-spec'd purchases and returns |
| No single source combines live market data, Cat specs, and job-site context | Operators, fleet managers | 1.6M connected machines but purchase decisions still rely on PDF brochures and tribal knowledge |
| Comparison reports are manually assembled in Word/Excel | Dealer principals | 3-5 hours per formal equipment proposal; limits throughput to ~2 proposals/day per rep |

**Revenue at stake**: Cat dealers influence ~$40B in annual machine/parts sales. Cutting recommendation time from 45 min to 2 min and improving match accuracy directly impacts close rates.

## 2. Synthetic Data

**No CSV/data files required.** All agents use live web search or generative synthesis:
- **SearchAgent** queries caterpillar.com, machinerytrader.com, and public spec sheets in real time.
- **DeepResearchAgent** aggregates search results into structured reports with citations.
- **AuthorAgent** formats from shared memory — no external data source needed.

This is intentional for the "quick win" demo: zero data prep, zero infrastructure, just YAML.

## 3. Agents Used

| Agent Name | Class | Role | Why This Class |
|-----------|-------|------|---------------|
| Equipment Search | `SearchAgent` | Real-time web lookup of Cat specs, pricing, availability | Zero code; returns raw facts from Google. Lightweight first pass. |
| Equipment Researcher | `DeepResearchAgent` | Multi-step research producing structured comparison reports with citations | Goes beyond single-query search — synthesizes multiple sources, adds section structure and inline citations. Far richer than SearchAgent alone. |
| Report Formatter | `AuthorAgent` | Polishes research output into a dealer-ready equipment recommendation document | Reads from shared memory (`research_output`), applies leading questions to shape tone/format for the audience (operator vs dealer vs fleet mgr). |
| Guardrails | `UtilityAgent` | Enforces Cat brand voice and filters non-equipment queries | Magic prompt template wraps every response in Cat-approved framing. Lightweight server-side — no round-trip to custom code. |

**Why not CustomAgent?** Every role maps to a built-in agent. CustomAgent would add Python maintenance burden with no functional gain.

## 4. Architecture Diagram

```
                         +------------------+
                         |   User Query     |
                         +--------+---------+
                                  |
                         +--------v---------+
                         |   Orchestrator   |
                         | enable_routing:  |
                         |   true           |
                         | decompose: true  |
                         +--+-----+-----+--+
                            |     |     |
              +-------------+  +--+--+  +---------------+
              |                |     |                  |
     +--------v--------+ +----v---+ +--------v--------+|
     | Equipment Search | | Guard- | | Equipment       ||
     | (SearchAgent)    | | rails  | | Researcher      ||
     |                  | | (Util) | | (DeepResearch)  ||
     +--------+---------+ +--------+ +--------+--------+|
              |                               |          |
              |        +-----------+          |          |
              +------->| Shared    |<---------+          |
                       | Memory    |                     |
                       +-----+-----+                     |
                             |                           |
                    +--------v---------+                 |
                    | Report Formatter |<----------------+
                    | (AuthorAgent)    |
                    +--------+---------+
                             |
                    +--------v---------+
                    | Formatted Report |
                    | w/ citations     |
                    +------------------+
```

## 5. Agent Configuration (Complete YAML)

```yaml
orchestrator:
  agent_list:
    - agent_name: "Equipment Search"
    - agent_name: "Equipment Researcher"
    - agent_name: "Report Formatter"
    - agent_name: "Guardrails"
  enable_routing: true
  decompose: true
  system_prompt_suffix: |
    You are the Cat AI Assistant, built for Caterpillar dealers, operators, and fleet managers.
    For simple factual questions (single spec, single model), route to Equipment Search.
    For comparison or recommendation queries, route to Equipment Researcher then Report Formatter.
    Always route through Guardrails before returning the final response.
  rai_config:
    blocked_topics: ["competitor disparagement", "safety workarounds", "price negotiation tactics"]

utility_agents:
  - agent_class: SearchAgent
    agent_name: "Equipment Search"
    agent_description: |
      Handles quick factual lookups: single-model specs, fuel consumption, operating weight,
      bucket capacity, engine horsepower, and availability. Routes to Google and returns
      concise answers from caterpillar.com and public equipment databases.

  - agent_class: DeepResearchAgent
    agent_name: "Equipment Researcher"
    agent_description: |
      Performs multi-step research for equipment comparisons, job-site recommendations,
      and fleet optimization questions. Produces structured reports with sections,
      data tables, and inline citations from multiple web sources.
    config:
      output_format: "html"
      memory_attribute_key: "research_output"
      max_research_steps: 5

  - agent_class: AuthorAgent
    agent_name: "Report Formatter"
    agent_description: |
      Formats the equipment research into a polished, dealer-ready recommendation document.
      Reads research from shared memory and structures it for the target audience.
    config:
      memory_attribute_key: "research_output"
      leading_questions:
        - "Who is the audience — operator, technician, dealer sales rep, or fleet manager?"
        - "Should the output emphasize TCO, productivity, or machine specs?"
        - "Are there site constraints (space, weight limits, elevation, climate)?"

  - agent_class: UtilityAgent
    agent_name: "Guardrails"
    agent_description: |
      Applies Caterpillar brand standards and filters off-topic queries.
    config:
      magic_prompt: |
        You are a Caterpillar brand compliance filter. Review the following response and ensure it:
        1. Uses official Cat model nomenclature (e.g., "Cat 320" not "Caterpillar 320 excavator")
        2. Includes safety disclaimers where relevant
        3. Does not make claims about competitor equipment
        4. Directs purchase/pricing questions to the nearest Cat dealer
        Response to review: {query}
```

## 6. Agent Flow

1. **Orchestrator** receives the user query and classifies it:
   - *Simple lookup* (e.g., "What is the operating weight of a Cat 336?") --> routes to **Equipment Search** --> passes through **Guardrails** --> returns answer.
   - *Complex comparison/recommendation* --> routes to **Equipment Researcher** --> researcher writes structured findings to **shared memory** under key `research_output` --> **Report Formatter** reads from that key and produces a polished document --> **Guardrails** validates brand compliance --> returns report.
2. **Decompose mode** allows the orchestrator to split multi-part queries (e.g., "Compare the D6 and D8 and recommend one for highway grading in Texas summers") into subtasks assigned in parallel where possible.
3. **Shared memory** is the bridge between Researcher and Formatter — no custom glue code needed.

## 7. Process Flow — Example Walkthroughs

### Query A: Simple Lookup
> "What is the fuel consumption of a Cat 745 articulated truck?"

| Step | Component | Action |
|------|-----------|--------|
| 1 | Orchestrator | Classifies as simple lookup; routes to Equipment Search |
| 2 | Equipment Search (SearchAgent) | Queries Google: `Cat 745 articulated truck fuel consumption specs site:caterpillar.com` |
| 3 | Equipment Search | Returns: "The Cat 745 has a fuel consumption of ~34 L/hr at standard load" |
| 4 | Guardrails (UtilityAgent) | Validates brand nomenclature, adds disclaimer: "Actual consumption varies by terrain and load" |
| 5 | Orchestrator | Returns final answer to user |

### Query B: Complex Comparison
> "We're bidding on a 200-acre solar farm grading job in Arizona. Compare Cat D6 vs D8 dozers — which is better for this project?"

| Step | Component | Action |
|------|-----------|--------|
| 1 | Orchestrator | Classifies as complex recommendation; routes to Equipment Researcher |
| 2 | Equipment Researcher (DeepResearchAgent) | Step 1: Searches D6 specs. Step 2: Searches D8 specs. Step 3: Searches "solar farm grading best practices." Step 4: Searches "Arizona heat equipment considerations." Step 5: Synthesizes into structured report with comparison table, pros/cons, and TCO estimate. Writes to shared memory `research_output`. |
| 3 | Report Formatter (AuthorAgent) | Reads `research_output`. Applies leading questions (audience=fleet manager, emphasis=TCO+productivity). Produces formatted recommendation with executive summary, comparison matrix, and "Recommended Configuration" section. |
| 4 | Guardrails (UtilityAgent) | Ensures Cat naming conventions, adds safety note about heat operations, directs pricing to local dealer. |
| 5 | Orchestrator | Returns polished report with inline citations to user |

### Query C: Off-Topic Rejection
> "How does the Komatsu PC200 compare to the Cat 320?"

| Step | Component | Action |
|------|-----------|--------|
| 1 | Orchestrator | Routes to Equipment Researcher |
| 2 | Equipment Researcher | Produces comparison focusing on Cat 320 capabilities |
| 3 | Guardrails | Strips direct competitor claims, reframes as "Cat 320 strengths for your use case," directs user to request a demo |
| 4 | Orchestrator | Returns brand-safe response |

## 8. AI Refinery Value Demonstrated

| Platform Capability | How This Demo Showcases It |
|---------------------|---------------------------|
| **Zero-code agent composition** | 4 agents, all built-in classes, configured entirely in YAML — no Python |
| **Intelligent routing** | Orchestrator auto-classifies simple vs complex queries and picks the right agent path |
| **Decomposition** | Multi-part questions are split into parallel subtasks automatically |
| **Shared memory** | DeepResearchAgent writes, AuthorAgent reads — decoupled pipeline with no custom integration |
| **DeepResearchAgent multi-step reasoning** | Goes far beyond a single LLM call: 5-step research with source triangulation and citations |
| **Brand guardrails (RAI)** | UtilityAgent + rai_config enforce compliance without custom middleware |
| **Audience-adaptive output** | AuthorAgent's leading_questions tailor the same research for different personas |

**Why this beats calling an LLM directly**: A raw LLM call cannot search the web for current specs, cannot produce cited multi-source reports, cannot enforce brand guardrails, and cannot adapt output format per audience — all without writing code. This demo proves that AI Refinery turns a weekend project into an enterprise-grade advisor.
