# OHSC Agent Quickstart

One command → activate → discover → use. For any external coding agent
(OpenCode, Claude Code, or any CLI agent) on this laptop.

## 1. Activate (one command)

```bash
ohsc activate
```

Expected (from any directory):

```
OHSC Capability Gateway
========================================
Status: ACTIVE

Capabilities:
  - Agent orchestration (Planner/Orchestrator/Reviewer)
  - Graphify (semantic knowledge graph)
  - Graphify Brain
  - Knowledge graph queries / shortest path / communities
  - Vault operations (read/write, authorized)
  - MCP (graph-navigation tools)

Graphify Brain:
  Backend: opencode
  Model:   opencode/hy3-free
  Key:     CONFIGURED (OPENCODE_API_KEY)
  OpenCode CLI: PRESENT
  Graphify: AVAILABLE (graphify 0.9.50)
```

If you see `Status: ACTIVE`, the gateway is ready.

## 2. Discover capabilities

```bash
ohsc capabilities --json      # full machine-readable manifest
ohsc status --json            # per-component health
ohsc agents                   # list the 16 registered agents
```

Prefer reading the static file `D:\HOSC\ohsc\capabilities.json` if you want to
avoid spawning a process. (Regenerate it with `ohsc capabilities --write`.)

## 3. Use Graphify (knowledge graph)

```bash
ohsc --graphify build "<vault>"            # semantic extraction (read-only vs vault)
ohsc --graphify analyze                     # hubs / communities / orphans / stats
ohsc --graphify query "how are A and B related?"
ohsc --graphify path --source A --target B # shortest conceptual path
ohsc --graphify explain "OpenCode"          # provenance + connections
```

Or use natural language (Planner routes graph phrasings to `graphify_agent`):

```bash
ohsc "find the shortest path between Agent and Community Detection"
ohsc "build a knowledge graph of my vault"
```

## 4. Write / create (requires authorization)

```bash
ohsc "create a MOC for Python tooling" --authorized
ohsc "create a note titled Changelog with content v2" --authorized
```

Writes target the **authorized vault** only. Graphify analysis is always
read-only against the vault.

## 5. Safety contracts (must respect)

- Real vault: `C:\Users\HAJI LAPTOP G55\Documents\Obsidian Vault` — never
  modify without explicit authorization.
- API keys (`OPENCODE_API_KEY`) are external; never print, log, or return them.
- Never fabricate graph results — every node/edge comes from real extraction.

## 6. Universal bootstrap protocol (recommended)

```
ohsc activate
ohsc capabilities --json
ohsc agents
```

That is the entire discover-and-use sequence for any coding agent.

## 7. Troubleshooting

| Symptom | Fix |
|---|---|
| `Graphify unavailable` | `uv tool install graphifyy` |
| `OPENCODE_API_KEY missing` | set the key in env (never commit) |
| `invalid model` | `GRAPHIFY_BRAIN_MODEL=opencode/hy3-free` |
| MCP tools skip | use `ohsc --graphify ...` CLI (MCP server needs `mcp` extras) |
| `0 edges but nodes present` | read `links`, not `edges` (graphify node_link format) |

See `docs/OHSC_UNIVERSAL_AGENT_GATEWAY.md` and `skills/OHSC_AGENT_SKILL.md`
for the full contract.
