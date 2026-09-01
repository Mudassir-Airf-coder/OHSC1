# Graph Report - advanced_vault  (2026-08-28)

## Corpus Check
- cluster-only mode — file stats not available

## Summary
- 34 nodes · 148 edges · 4 communities
- Extraction: 100% EXTRACTED · 0% INFERRED · 0% AMBIGUOUS
- Token cost: 197 input · 18 output

## Community Hubs (Navigation)
- Knowledge Graph
- AI Agent
- Knowledge Graph Engineering
- Orchestrator

## God Nodes (most connected - your core abstractions)
1. `Knowledge Graph` - 28 edges
2. `AI Agent` - 28 edges
3. `Graphify` - 18 edges
4. `Graph Engineering` - 13 edges
5. `Obsidian` - 13 edges
6. `Machine Learning` - 11 edges
7. `Orchestrator` - 11 edges
8. `LLMs` - 10 edges
9. `Evaluation` - 10 edges
10. `Semantic Retrieval` - 10 edges

## Surprising Connections (you probably didn't know these)
- `Typography` --references--> `Obsidian`  [EXTRACTED]
  Typography.md → Obsidian.md
- `AI Agent` --references--> `Artificial Intelligence`  [EXTRACTED]
  AI Agent.md → Artificial Intelligence.md
- `Artificial Intelligence` --references--> `Graph Engineering`  [EXTRACTED]
  Artificial Intelligence.md → Graph Engineering.md
- `Artificial Intelligence` --references--> `Graphify`  [EXTRACTED]
  Artificial Intelligence.md → Graphify.md
- `Artificial Intelligence` --references--> `LLMs`  [EXTRACTED]
  Artificial Intelligence.md → LLMs.md

## Hyperedges (group relationships)
- **Agent Tooling & Orchestration** — ai_agent, mcp, automation, evaluation [INFERRED 0.75]
- **AI Agent Core Stack** — ai_agent, artificial_intelligence, machine_learning, knowledge_graph, deep_learning, llms [INFERRED 0.75]
- **AI Agent System Flow** — ai_agent, orchestrator, reviewer, planner, tool_use [INFERRED 0.75]
- **Knowledge Graph Ecosystem** — knowledge_graph, graphify, graph_engineering, graph_databases [INFERRED 0.75]
- **Obsidian Knowledge Base Management** — obsidian, knowledge_graph, wikilinks, graphify, vault_automation, semantic_retrieval [INFERRED 0.75]
- **Retrieval Augmented Generation Stack** — retrieval_augmented_generation, llms, semantic_retrieval, vector_search, knowledge_graph [INFERRED 0.75]

## Communities (4 total, 0 thin omitted)

### Community 0 - "Knowledge Graph"
Cohesion: 0.47
Nodes (6): Artificial Intelligence, Cognitive Science, Data Pipeline, Gardening, Graph Databases, Knowledge Graph

### Community 1 - "AI Agent"
Cohesion: 0.64
Nodes (9): AI Agent, Deep Learning, Embeddings, Evaluation, LLMs, Machine Learning, Prompt Engineering, Reinforcement Learning (+1 more)

### Community 3 - "Knowledge Graph Engineering"
Cohesion: 0.56
Nodes (10): Graph Engineering, Graphify, Knowledge Management, Neural Networks, Obsidian, Ontology, Semantic Retrieval, Vault Automation (+2 more)

### Community 4 - "Orchestrator"
Cohesion: 0.47
Nodes (9): Automation, MCP, Multi-Agent Systems, Orchestrator, Planner, Reviewer, Software Architecture, Tool Use (+1 more)

## Knowledge Gaps
- **1 isolated node(s):** `Gardening`
  These have ≤1 connection - possible missing edges or undocumented components.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `Knowledge Graph` connect `Knowledge Graph` to `AI Agent`, `Knowledge Graph Engineering`, `Orchestrator`?**
  _High betweenness centrality (0.261) - this node is a cross-community bridge._
- **Why does `AI Agent` connect `AI Agent` to `Knowledge Graph`, `Knowledge Graph Engineering`, `Orchestrator`?**
  _High betweenness centrality (0.232) - this node is a cross-community bridge._
- **Why does `Obsidian` connect `Knowledge Graph Engineering` to `Knowledge Graph`, `AI Agent`, `Orchestrator`?**
  _High betweenness centrality (0.063) - this node is a cross-community bridge._
- **What connects `Gardening` to the rest of the system?**
  _1 weakly-connected nodes found - possible documentation gaps or missing edges._