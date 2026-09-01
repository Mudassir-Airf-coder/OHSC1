# Graph Report - basic_vault  (2026-08-28)

## Corpus Check
- cluster-only mode — file stats not available

## Summary
- 9 nodes · 28 edges · 2 communities
- Extraction: 100% EXTRACTED · 0% INFERRED · 0% AMBIGUOUS
- Token cost: 120 input · 15 output

## Community Hubs (Navigation)
- AI & Knowledge Graphs
- Graph Engineering

## God Nodes (most connected - your core abstractions)
1. `AI Agent` - 8 edges
2. `Knowledge Graph` - 8 edges
3. `Graph Engineering` - 7 edges
4. `Obsidian` - 7 edges
5. `Artificial Intelligence` - 6 edges
6. `Graphify` - 6 edges
7. `Neural Networks` - 5 edges
8. `Wikilinks` - 5 edges
9. `Machine Learning` - 4 edges

## Surprising Connections (you probably didn't know these)
- `AI Agent` --references--> `Graph Engineering`  [EXTRACTED]
  AI Agent.md → Graph Engineering.md
- `AI Agent` --references--> `Graphify`  [EXTRACTED]
  AI Agent.md → Graphify.md
- `AI Agent` --references--> `Obsidian`  [EXTRACTED]
  AI Agent.md → Obsidian.md
- `Wikilinks` --references--> `AI Agent`  [EXTRACTED]
  Wikilinks.md → AI Agent.md
- `Artificial Intelligence` --references--> `Graph Engineering`  [EXTRACTED]
  Artificial Intelligence.md → Graph Engineering.md

## Hyperedges (group relationships)
- **AI Knowledge Graph Stack** — ai_agent, knowledge_graph, graphify, obsidian, wikilinks, graph_engineering [INFERRED 0.75]
- **Foundations of AI** — artificial_intelligence, machine_learning, neural_networks [INFERRED 0.75]

## Communities (2 total, 0 thin omitted)

### Community 0 - "AI & Knowledge Graphs"
Cohesion: 0.90
Nodes (5): AI Agent, Artificial Intelligence, Knowledge Graph, Machine Learning, Neural Networks

### Community 1 - "Graph Engineering"
Cohesion: 1.00
Nodes (4): Graph Engineering, Graphify, Obsidian, Wikilinks

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `AI Agent` connect `AI & Knowledge Graphs` to `Graph Engineering`?**
  _High betweenness centrality (0.077) - this node is a cross-community bridge._
- **Why does `Knowledge Graph` connect `AI & Knowledge Graphs` to `Graph Engineering`?**
  _High betweenness centrality (0.077) - this node is a cross-community bridge._
- **Why does `Obsidian` connect `Graph Engineering` to `AI & Knowledge Graphs`?**
  _High betweenness centrality (0.049) - this node is a cross-community bridge._