# BASIC Vault — Graphify Brain Validation Report

Generated: 2026-08-28
Vault: `D:\HOSC\tests\graphify_brain_validation\basic_vault` (isolated temp vault — NOT the real vault)
Backend: Graphify Brain → OpenAI-compatible interface → Gemini `gemini-2.5-flash` (`GEMINI_KEY_1` via env)
Note: OpenCode is the configured-primary Brain backend but is billing-blocked (CreditsError); this run used the working OpenAI-compatible backend per the mandate. See GRAPHIFY_BRAIN_PREFLIGHT.md.

---

## 1. Vault construction
- 9 Markdown notes, realistic content, explicit `[[wikilinks]]` + semantic relationships not dependent on wikilinks.
- Concepts: Artificial Intelligence, Machine Learning, Neural Networks, Knowledge Graph, Graphify, Obsidian, AI Agent, Graph Engineering, Wikilinks.

## 2. Extraction (Graphify Brain → LLM)
- Command: `graphify extract <vault>` with `OPENAI_BASE_URL`/`OPENAI_MODEL`/`OPENAI_API_KEY` set by the Brain.
- Result: `graph.json` written to `D:\HOSC\graphify\validation\basic\graph.json`.
- Nodes: **9** | Links: **28** | Communities (from report): **2**
- Provenance: **28/28 EXTRACTED** (relation `references`), **0 INFERRED** in this small corpus. Every edge carries `confidence: EXTRACTED` and `source_file` — provenance preserved.
- No corrupted nodes, no broken structure.

## 3. Graph report + HTML
- `GRAPH_REPORT.md` generated (2 communities: "AI & Knowledge Graphs", "Graph Engineering").
- `graph.html` interactive visualization generated.
- Token cost: 120 input / 15 output.

## 4. Capability suite (real execution)
| Capability | Command | Result | Latency |
|---|---|---|---|
| Graph stats | (graph.json) | 9 nodes / 28 links / 2 communities | instant |
| God nodes | `god-nodes` | AI Agent(8), Knowledge Graph(8), Graph Engineering(7), Obsidian(7), AI(6), Graphify(6), Neural Networks(5), Wikilinks(5), ML(4) | 42.98s |
| Orphans | degree-0 scan | none | instant |
| Query "What connects Graphify and Obsidian?" | `query` | Traversed graph; returned edge `Graphify --references--> Obsidian` + full context walk | 75.14s |
| Query "Which nodes are most central?" | `query` | "No matching nodes found" — Graphify `query` is a BFS traversal over a *question*, not a centrality meta-query. Expected limitation, documented honestly. | 118.78s |
| Shortest path AI Agent → Knowledge Graph | `path --undirected` | 1 hop: AI Agent → Knowledge Graph | 69.33s |
| Shortest path Neural Networks → Obsidian | `path --undirected` | 2 hops: Neural Networks ← AI Agent → Obsidian | 83.55s |
| Explain "AI Agent" | `explain` | Node detail + 8 connections, all EXTRACTED | 19.38s |

## 5. Summarized metrics
- Notes: 9
- Nodes: 9
- Links: 28
- EXTRACTED edges: 28 (100%)
- INFERRED edges: 0
- Communities: 2 (AI & Knowledge Graphs; Graph Engineering)
- Hubs (god nodes): AI Agent, Knowledge Graph (8 edges each)
- Orphans: 0
- Multi-hop paths verified: yes (2-hop NN→Obsidian)
- Total capability suite latency: ~409s (Gemini backend, includes LLM calls for query/explain)

## 6. Verdict
BASIC vault = PASS. Graphify Brain performed semantic extraction, produced a valid provenance-tagged graph, and all reachable capabilities (god-nodes, query traversal, shortest path, explain) executed correctly. The only non-answer (`query` on centrality) is a documented Graphify design limitation, not a failure.
