# Graphify Integration — OHSC

## What is Graphify?

[Graphify](https://github.com/Graphify-Labs/graphify) is a knowledge-graph
tool that turns a folder of mixed content (markdown, code, PDFs, images) into a
**queryable graph**: `graph.json`, `graph.html` visualization, and a
`GRAPH_REPORT.md`. It extracts both **EXTRACTED** (explicit — e.g. a wikilink
the note actually contains) and **INFERRED** (semantic — discovered by the
model) relationships.

Installed build used in this integration: **graphify 0.9.50**
(`graphifyy` PyPI package; CLI `graphify`, MCP `graphify-mcp`).

## Why OHSC uses it

OHSC already has a **Linking Agent** for *structural* Obsidian relationships
(`[[wikilinks]]`, broken links, orphans, backlinks). Graphify adds a second,
complementary layer of **semantic graph intelligence**:

| Layer | Agent | Owns |
|-------|-------|------|
| Structural Obsidian links | `linking_agent` | explicit `[[wikilinks]]`, repairs, hub/orphan detection |
| Semantic graph intelligence | `graphify_agent` | inferred/extracted relationships, traversal, shortest path, communities, explanation |
| Human navigation | `dashboard_agent` | MOCs / indexes |
| Verification | `reviewer_agent` | structured approval |

Graphify's semantic graph is a **different layer** from Obsidian's wikilink
graph. An inferred relationship is **never** automatically turned into a
wikilink — only the Linking Agent modifies notes, and only after an explicit
request.

## Architecture

```
                  OHSC Orchestrator
                          |
                     Planner (INTENT_RULES)
                          |
               +----------+-----------+
               |                      |
          linking_agent          graphify_agent
               |                      |
          Wikilinks            +-------+--------+
                               |                |
                        Graphify Client   Graphify MCP Client
                               |                |
                          graphify CLI     graphify-mcp server
                               |
                          graph.json  (in D:\HOSC\graphify\graphs)
```

- `ohsc/agents/graphify_agent.py` — the only module that knows how Graphify works.
- `ohsc/integrations/graphify/` — adapter layer (isolates all Graphify subprocess
  calls):
  - `graphify_client.py` — CLI wrapper (extract / query / path / explain). Strips
    `PYTHONPATH` so Graphify resolves its own numpy/openai (host venv shadowing fix).
  - `graphify_runner.py` — build / incremental / caching lifecycle + graph queries.
  - `graphify_mcp.py` — MCP stdio client (relevant tools only).
  - `graphify_config.py` — workspace paths (all under `D:\HOSC\graphify`).
  - `graphify_models.py` — `EdgeKind` (EXTRACTED/INFERRED), node/edge models.

## Installation (as actually performed)

```bash
uv tool install "graphifyy[mcp]" --force
# Requires an LLM key for semantic extraction of markdown:
#   GEMINI_API_KEY / GOOGLE_API_KEY / OPENAI_API_KEY / etc.
# Also requires the `openai` package for the gemini backend inside the tool venv:
#   uv tool install "graphifyy[gemini]" --force
```

### Environment fixes applied (real, required)

1. **numpy ABI crash** — Graphify's bundled numpy was rebuilt against the wrong
   Python ABI. Fixed by `pip install --force-reinstall --no-deps numpy` inside the
   tool venv.
2. **PYTHONPATH shadowing** — the host (Hermes agent) venv exports `PYTHONPATH`
   that shadows Graphify's numpy/openai. The `GraphifyClient` runs every
   subprocess with `PYTHONPATH` removed so Graphify always uses its own deps.
3. **`mcp` package** — `graphifyy[mcp]` did not pull `mcp` in this environment;
   installed it into the tool venv so `graphify-mcp` starts.

## Configuration

Graphify data lives **only** under `D:\HOSC\graphify`:

```
D:\HOSC\graphify\
    graphs/     graph.json (built graph)
    reports/    GRAPH_REPORT.md, graph.html
    cache/
    exports/    (opt-in Obsidian export — never into the real vault)
    logs/
    config/     graph_meta.json (caching metadata)
```

## CLI Usage

Natural-language (routed by Planner → graphify_agent):

```bash
python -m ohsc.cli --authorized "Analyze the knowledge graph of this vault"
python -m ohsc.cli --authorized "Find the shortest path between OHSC and Loop Engineering"
python -m ohsc.cli --authorized "Find graph hubs"
```

Direct mode (hides Graphify internals):

```bash
python -m ohsc.cli --authorized --graphify build
python -m ohsc.cli --authorized --graphify query "What connects Graph Engineering to Knowledge Graph"
python -m ohsc.cli --authorized --graphify path --source "OHSC" --target "Loop Engineering"
python -m ohsc.cli --authorized --graphify explain --node "OHSC"
```

## MCP Usage

```bash
graphify-mcp <path-to>/graph.json
```

OHSC's `GraphifyMCPClient` exposes the vault-relevant tools:
`query_graph`, `get_node`, `get_neighbors`, `god_nodes`, `graph_stats`,
`shortest_path`, `get_community`. The PR-specific tools (`list_prs`,
`get_pr_impact`, `triage_prs`) are code-repo specific and intentionally
excluded.

## Routing Behavior

`ohsc/core/planner.py` `INTENT_RULES` places Graphify keywords **first** so
phrases like "find relationships", "find the shortest path", "find graph hubs"
route to `graphify_agent` instead of the generic `search_agent`. The Planner
also extracts structured params (e.g. source/target for `shortest_path`).

## Graph Caching

`GraphifyRunner` caches `graph.json` under `D:\HOSC\graphify/graphs` and records
`graph_meta.json` (graph version, vault mtime, build timestamp). On a query it
**reuses** a valid cached graph instead of rebuilding. If the vault's mtime
advances, or the graph is missing/corrupted, it rebuilds. Correctness is
preserved: the real vault is always authoritative.

## Safety Model

- **READ-ONLY on the vault by default.** A graph request only *reads* the vault
  and writes Graphify artifacts into `D:\HOSC\graphify` — never into the vault.
- **PathSafety** remains authoritative; the agent refuses to run if the
  configured `vault_root` does not exist or is not an Obsidian vault
  (`VAULT PATH MISMATCH`).
- **No silent fallback.** Unavailable binary → `GRAPHIFY UNAVAILABLE`; missing
  graph → `GRAPH NOT BUILT`; stale → rebuild path.
- **Provenance preserved.** EXTRACTED vs INFERRED edges are kept distinct in
  responses; inferred links are never presented as explicit facts.

## Error Handling

Every failure returns a structured `AgentResult` (no crash, no internal
stack trace leaked to the user). Verified cases: missing graph, corrupt graph,
unavailable binary, vault mismatch, empty vault, unauthorized request.

## Tests

`tests/test_graphify_*.py` (installation, config, runner, agent, mcp,
vault_safety, routing). Full suite: **50 passed** (16 existing + 34 Graphify).

## Performance (measured)

- First build (extract + cluster, 11-node vault, Gemini): ~6 s
- Cached rebuild avoided: 0 s (reuses graph.json)
- Query (BFS): ~3 s
- CLI route → agent → query: a few seconds end-to-end
- Reuse vs rebuild is deterministic via `graph_meta.json` vault mtime check.

## Known Limitations

- Semantic extraction requires an external LLM key (no offline semantic mode).
- `--code-only` skips markdown (so a no-key build yields an empty graph).
- `graphify path` is directed by default; OHSC passes `--undirected` because
  wikilinks are bidirectional for knowledge discovery.
- Graphify MCP server must run inside Graphify's own uv-tool venv (host
  `PYTHONPATH` stripped by the adapter).
