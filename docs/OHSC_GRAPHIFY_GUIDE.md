# OHSC Graphify Guide

Using Graphify through OHSC — semantic knowledge-graph extraction and analysis
over an Obsidian vault.

## What Graphify produces

- `graph.json` — networkx node_link format. **Edges are under the `links`
  key** (not `edges`); nodes under `nodes`; per-node `community` attribute;
  hyperedges under `hyperedges`.
- `graph.html` — interactive visualization.
- `GRAPH_REPORT.md` — hubs, communities, orphans, stats.

Provenance: every edge has a `confidence` flag — `EXTRACTED` (explicit, e.g. a
real wikilink) vs `INFERRED` (semantic, discovered by the model). OHSC never
presents an INFERRED link as a fact.

## Operations (all via `graphify_agent`)

| Command | Operation | Read-only |
|---|---|---|
| `ohsc --graphify build "<vault>"` | semantic extraction → graph artifacts | yes (vs vault) |
| `ohsc --graphify query "..."` | NL question over graph (BFS, community-aware) | yes |
| `ohsc --graphify path --source A --target B` | shortest conceptual path (undirected) | yes |
| `ohsc --graphify explain "<node>"` | provenance + connections | yes |
| `ohsc --graphify analyze` | hubs / communities / orphans / stats | yes |

## Graphify Brain (the LLM backend)

- **Backend:** OpenCode (`opencode run` CLI).
- **Model:** `opencode/hy3-free`.
- **Transport:** prompt piped via **STDIN** (Windows argv length limit makes
  argv passing unreliable for large prompts).
- **Config env:** `GRAPHIFY_BRAIN_BACKEND=opencode`,
  `GRAPHIFY_BRAIN_MODEL=opencode/hy3-free`, `OPENCODE_API_KEY` (external,
  never printed).
- **Failure behavior:** empty/filtered response → graphify surfaces a clean
  error; proxy never leaks key material.

## Measured performance (OpenCode CLI)

| Vault | Nodes | Links | Time |
|---|---|---|---|
| basic | 29 | 19 | 57.6s |
| intermediate | 19 | 34 | 76.4s |
| advanced | 41 | 89 | 84.1s |

(Cached re-runs reuse the built graph; a single shortest-path query over a
built graph takes ~7.7s — graphify CLI cold start.)

## Graph artifacts location

Artifacts are written ONLY under `D:\HOSC\graphify\graphs\<vault>\` — never
inside the user's vault.

## MCP (optional)

If `graphify-mcp` is available, OHSC exposes `query_graph`, `get_node`,
`get_neighbors`, `god_nodes`, `graph_stats`, `shortest_path`, `get_community`.
PR tools (`list_prs`, `get_pr_impact`, `triage_prs`) are excluded (code-repo
specific). When the MCP server cannot start, the CLI path is used instead; the
tests for MCP are skipped honestly.
