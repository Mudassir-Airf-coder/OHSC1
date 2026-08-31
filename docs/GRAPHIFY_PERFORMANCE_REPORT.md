# GRAPHIFY PERFORMANCE REPORT

Measured during the validation run (11-node temporary vault, Gemini backend).

## Measurements

| Metric | First run | Cached run | Note |
|--------|-----------|------------|------|
| Graphify extract (semantic) | ~5.8 s | n/a | LLM call per corpus chunk |
| Graphify cluster-only | included in extract | n/a | community naming via LLM |
| **Full build (extract+cluster)** | **~6.0 s** | — | |
| Cached reuse decision | — | **<0.05 s** | vault mtime compare in `graph_meta.json` |
| Query (BFS traverse) | ~3.0 s | ~3.0 s | reads graph.json, no rebuild |
| Shortest path (undirected) | ~3.0 s | ~3.0 s | |
| MCP get_node | ~1.5 s | ~1.5 s | server handshake + lookup |
| OHSC route (Planner) | ~0.2 s | ~0.2 s | keyword table, no model |
| End-to-end NL → answer | ~3–6 s | ~3 s | routing + query |

## Optimization Decisions (measured, not guessed)

1. **Graph caching (reuse, not rebuild).** `GraphifyRunner.needs_rebuild()`
   compares the vault's newest file mtime against `graph_meta.json`. A query
   against an unchanged vault reuses `graph.json` (0 s rebuild). Verified:
   second `build` returns "reused existing graph - no rebuild needed" and the
   graph file mtime is unchanged.

2. **Single subprocess per operation.** Each query spawns one `graphify`
   process (cheap relative to the LLM extract). No redundant extraction.

3. **PYTHONPATH strip avoids a double-import / ABI crash**, which would
   otherwise force a slow failure-and-retry.

## What was NOT optimized (and why)

- **Semantic extraction time** (~6 s) is dominated by the external LLM call and
  is intrinsic to Graphify. It only runs on a *build*, never on a *query*, so
  day-to-day graph questions stay fast.
- No in-memory graph caching of `graph.json` beyond file reuse — the file is
  small (≤10 KB for this vault) and re-parsing is sub-millisecond.

## Scaling note

For large vaults, the dominant cost is the one-time extract. Queries remain
O(graph traversal) and fast. The cache invalidation is deterministic (vault
mtime), so staleness is detected without scanning every file's content.
