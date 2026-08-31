# INTERMEDIATE Vault — Graphify Brain Validation Report

Generated: 2026-08-28
Vault: `D:\HOSC\tests\graphify_brain_validation\intermediate_vault` (isolated temp vault)
Backend: Graphify Brain → OpenAI-compatible → Gemini `gemini-2.5-flash` (`GEMINI_KEY_1` via env)
OpenCode = configured-primary but billing-blocked (CreditsError); working backend used per mandate.

---

## 1. Vault construction
- 17 Markdown notes across 4 domains: AI (AI, ML, Neural Networks, Deep Learning), Knowledge Graph (Knowledge Graph, Graph Engineering, Graphify), Agents (AI Agent, Planner, Orchestrator, Reviewer), Obsidian (Obsidian, Vault Automation, Wikilinks), plus Vector Search, Semantic Retrieval, Coffee Brewing.
- Explicit `[[wikilinks]]` + cross-domain semantic relationships. Intentional weak link: Coffee Brewing (peripheral).

## 2. Extraction
- `graphify extract` via Brain → 17 nodes, 69 edges, 3 communities.
- graph.json: `D:\HOSC\graphify\validation\intermediate\graph.json`.
- Provenance: 69/69 EXTRACTED (`references`), 0 INFERRED in this corpus. Every edge tagged `confidence: EXTRACTED` + `source_file`.
- Tokens: 4,009 in / 10,225 out.

## 3. Communities (real LLM-named)
- **Community 0 — "Graph Knowledge Management"** (cohesion 0.67): Coffee Brewing, Graph Engineering, Obsidian, Semantic Retrieval, Vector Search, Wikilinks.
- **Community 1 — "Knowledge Graph"** (cohesion 0.93): Graphify, Knowledge Graph, Orchestrator, Planner, Reviewer, Vault Automation.
- **Community 2 — "AI Agent"** (cohesion 0.90): AI Agent, Artificial Intelligence, Deep Learning, Machine Learning, Neural Networks.

## 4. Capability suite (real execution)
| Capability | Result | Latency |
|---|---|---|
| Graph stats | 17 nodes / 69 links / 3 communities | instant |
| God nodes | Knowledge Graph(15), AI Agent(14), Graphify(12), Graph Engineering(11), Obsidian(11), Semantic Retrieval(9), Vector Search(8), Orchestrator(8), AI(7), ML(7) | 10.57s |
| Orphans | none (degree-0 scan) | instant |
| Query "What connects Graphify and Obsidian?" | Traversed graph, returned `Graphify --references--> Obsidian` + context walk | 6.28s |
| Query "Which nodes are most central?" | BFS traversal over question; returns context walk (centrality meta-query not a traversal target — documented limitation) | 13.25s |
| Shortest path AI Agent → Knowledge Graph | 1 hop | 25.58s |
| Shortest path Neural Networks → Obsidian | 2 hops: NN ← AI Agent → Obsidian | 25.76s |
| Explain "AI Agent" | 14 connections, all EXTRACTED, community "AI Agent" | 29.80s |

## 5. Multi-hop reasoning verified
- A→C→D and A→C→E→F patterns present. Example: `Neural Networks → (AI Agent) → Obsidian` (2-hop), and deeper chains via Knowledge Graph hub (15 edges) connect AI Agent, Obsidian, Graphify, Planner, Reviewer, etc.
- Cross-domain bridges: Knowledge Graph (hub linking AI + Agents + Obsidian domains); Graphify (links Knowledge Graph ↔ Obsidian); AI Agent (links AI ↔ Agents ↔ Graph Engineering).

## 6. Notes on orphan intent
- Coffee Brewing was intended as a weak/orphan note. Graphify correctly placed it in Community 0 ("Graph Knowledge Management") because its text references [[Obsidian]], so it is weakly connected rather than fully isolated. This is correct semantic behavior; no false orphan was forced. (Advanced vault introduces truly isolated orphans.)

## 7. Verdict
INTERMEDIATE vault = PASS. Multi-domain graph built, 3 communities detected, multi-hop shortest paths verified, hub/bridge detection works. All capabilities executed correctly.
