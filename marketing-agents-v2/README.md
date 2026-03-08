# Marketing Agents Demo

Demonstrates a **FlowSuperAgent** DAG that orchestrates 6 agents to research a topic, develop a marketing strategy, write a report, and save it to disk.

## Architecture

```
User Query
    |
    +---> Web Searcher (MCPClientAgent / DuckDuckGo)  ---+
    +---> Paper Searcher (MCPClientAgent / arXiv)      ---+--> Marketing Strategist (PlanningAgent)
    +---> News Searcher (SearchAgent)                  ---+           |
                                                          Report Writer (AuthorAgent)
                                                                      |
                                                          Filesystem Agent (MCPClientAgent)
```

## Prerequisites

- Node.js (for Filesystem MCP server)
- Ports 4001, 4003, 4004, 8000 must be free

## Setup

```bash
source venv/bin/activate
```

## Run

Use `start.sh` which starts all MCP servers and the web UI:

```bash
bash start.sh
# Open http://localhost:8000
```

This starts:
1. DuckDuckGo MCP server on port 4003
2. arXiv MCP server on port 4001
3. Filesystem MCP server on port 4004
4. FastAPI web UI on port 8000

## Example Prompts

- "Generate a marketing campaign for Agentic AI enterprise adoption"
- "Create a go-to-market strategy for a new cloud security product"
- "Develop a marketing plan for a healthcare AI startup"

## Notes

- The full pipeline takes 2-3 minutes to complete
- The Report Writer produces a structured markdown report in 4 sections
- The Filesystem Agent saves the report as `marketing_report_YYYY-MM-DD.md`
