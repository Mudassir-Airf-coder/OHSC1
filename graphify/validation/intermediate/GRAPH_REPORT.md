# Graph Report - intermediate_vault  (2026-08-28)

## Corpus Check
- cluster-only mode — file stats not available

## Summary
- 17 nodes · 69 edges · 3 communities
- Extraction: 100% EXTRACTED · 0% INFERRED · 0% AMBIGUOUS
- Token cost: 146 input · 13 output

## Community Hubs (Navigation)
- Graph Knowledge Management
- Knowledge Graph
- AI Agent

## God Nodes (most connected - your core abstractions)
1. `Knowledge Graph` - 15 edges
2. `AI Agent` - 14 edges
3. `Graphify` - 12 edges
4. `Graph Engineering` - 11 edges
5. `Obsidian` - 11 edges
6. `Semantic Retrieval` - 9 edges
7. `Vector Search` - 8 edges
8. `Orchestrator` - 8 edges
9. `Artificial Intelligence` - 7 edges
10. `Machine Learning` - 7 edges

## Surprising Connections (you probably didn't know these)
- `Coffee Brewing` --references--> `Obsidian`  [EXTRACTED]
  Coffee Brewing.md → Obsidian.md
- `AI Agent` --references--> `Graph Engineering`  [EXTRACTED]
  AI Agent.md → Graph Engineering.md
- `Artificial Intelligence` --references--> `Graph Engineering`  [EXTRACTED]
  Artificial Intelligence.md → Graph Engineering.md
- `Graph Engineering` --references--> `Graphify`  [EXTRACTED]
  Graph Engineering.md → Graphify.md
- `Graph Engineering` --references--> `Knowledge Graph`  [EXTRACTED]
  Graph Engineering.md → Knowledge Graph.md

## Hyperedges (group relationships)
- **AI Agent Execution Flow** — ai_agent, planner, orchestrator, reviewer [INFERRED 0.75]
- **Core AI Concepts** — artificial_intelligence, machine_learning, neural_networks, deep_learning, ai_agent, knowledge_graph [INFERRED 0.75]
- **Knowledge Management Stack** — obsidian, graphify, wikilinks, knowledge_graph, graph_engineering [INFERRED 0.75]

## Communities (3 total, 0 thin omitted)

### Community 0 - "Graph Knowledge Management"
Cohesion: 0.67
Nodes (6): Coffee Brewing, Graph Engineering, Obsidian, Semantic Retrieval, Vector Search, Wikilinks

### Community 1 - "Knowledge Graph"
Cohesion: 0.93
Nodes (6): Graphify, Knowledge Graph, Orchestrator, Planner, Reviewer, Vault Automation

### Community 2 - "AI Agent"
Cohesion: 0.90
Nodes (5): AI Agent, Artificial Intelligence, Deep Learning, Machine Learning, Neural Networks

## Knowledge Gaps
- **1 isolated node(s):** `Coffee Brewing`
  These have ≤1 connection - possible missing edges or undocumented components.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `Obsidian` connect `Graph Knowledge Management` to `Knowledge Graph`, `AI Agent`?**
  _High betweenness centrality (0.151) - this node is a cross-community bridge._
- **Why does `Knowledge Graph` connect `Knowledge Graph` to `Graph Knowledge Management`, `AI Agent`?**
  _High betweenness centrality (0.144) - this node is a cross-community bridge._
- **Why does `AI Agent` connect `AI Agent` to `Graph Knowledge Management`, `Knowledge Graph`?**
  _High betweenness centrality (0.116) - this node is a cross-community bridge._
- **What connects `Coffee Brewing` to the rest of the system?**
  _1 weakly-connected nodes found - possible documentation gaps or missing edges._