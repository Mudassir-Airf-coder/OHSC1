# OHSC Universal Agent Capability Gateway

One-command activation layer that exposes the OHSC (Hermes Obsidian System
Control) capability engine to **any external coding/AI agent** — OpenCode,
Claude Code, or any CLI — without rebuilding OHSC.

## Why

OHSC already provides a 16-agent control plane, Graphify semantic graphs, and
Graphify Brain (LLM backend). Agents that want to *use* OHSC shouldn't have to
learn its internals. The Gateway is a thin, stdlib-only discovery + activation
layer that:

1. Confirms the engine is installed, configured, and healthy (`ohsc activate`).
2. Publishes a machine-readable capability manifest (`ohsc capabilities`).
3. Routes natural-language requests through the Planner → Orchestrator → Agents
   pipeline (`ohsc "<request>"`).
4. Exposes Graphify operations directly (`ohsc --graphify ...`).

It is **not** hard-wired to one agent. The manifest advertises every capability
and its responsible agent; any client can discover and call them.

## Activation (one command)

```bash
ohsc activate
```

Returns `Status: ACTIVE` when: installation present, Python present, config
valid, agent registry loads (16 agents), Graphify available (0.9.50), Graphify
Brain backend online (OpenCode / `opencode/hy3-free`), and `OPENCODE_API_KEY`
configured.

The `ohsc` command resolves `D:\HOSC` from **any working directory** via a shim
in `~/.local/bin` (`ohsc` for git-bash, `ohsc.cmd` for CMD/PowerShell).

## Discovery

```bash
ohsc capabilities            # human-readable summary
ohsc capabilities --json     # full machine-readable manifest
ohsc status --json          # per-component health checks
ohsc agents                 # list the 16 registered agents
```

Manifest shape (`ohsc/gateway.py::capability_manifest`):

```jsonc
{
  "ohsc": {"root": "D:\\HOSC", "version": "..."},
  "capability_groups": {
    "graphify": {
      "llm_backend": "opencode",
      "model": "opencode/hy3-free",
      "operations": [ {"name":"build_graph", ...}, ... ],
      "mcp_tools": ["query_graph", ...]
    },
    "vault":   { "operations": [ ... ] },
    "notes":   { "operations": [ ... ] }
  },
  "interfaces": {"cli": "...", "mcp": "...", "python_api": "..."},
  "agents": [ {"name":"graphify_agent", ...}, ... ]   // 16 agents
}
```

## Natural-language usage

```bash
ohsc "find the shortest path between Agent and Community Detection"
ohsc --graphify build "<vault>"
ohsc --graphify query "how do agents communicate"
ohsc --graphify path --source Agent --target Graphify
ohsc --graphify explain OpenCode
ohsc --graphify analyze
```

Routing: graph-specific phrasings are mapped to `graphify_agent` first via
`ohsc/core/planner.py::INTENT_RULES` (see "shortest path", "knowledge graph",
"communities", "explain how", …). Generic intents fall through to the matching
vault/note/search agent.

## Programmatic usage

```python
import ohsc
rt = ohsc.build_runtime()
# dispatch a request through the orchestrator
result = rt.workflow.run("analyze my vault")
# or use integrations directly
from ohsc.integrations.graphify import GraphifyRunner
```

## Capability groups

| Group | Operations | Notes |
|---|---|---|
| `graphify` | build_graph, query_graph, shortest_path, explain, analyze | semantic knowledge graph (Graphify Brain → OpenCode/hy3-free) |
| `vault` | snapshot, transaction/rollback, audit | safety-first |
| `notes` | create/read/update/delete | write needs `--authorized` |
| `search` | full-text / semantic search | read-only |
| `linking` | wikilink edit, orphan analysis | write needs `--authorized` |
| `metadata` | frontmatter / YAML props | write needs `--authorized` |
| `templates` | note templates | write needs `--authorized` |
| `periodic` | daily/weekly notes | write needs `--authorized` |
| `canvas` | canvas boards | write needs `--authorized` |
| `dashboard` | MOC / dashboard | write needs `--authorized` |
| `bulk` | bulk edits | destructive — authorized only |
| `reviewer` | post-hoc verification | read-only |

## Safety

- Real vault: `C:\Users\HAJI LAPTOP G55\Documents\Obsidian Vault` is **read-only**
  for Graphify analysis; artifacts land only under `D:\HOSC\graphify\graphs\`.
- Write/destructive ops require explicit authorization (`--authorized`).
- `safety_mode: strict` in config.
- Test vaults live in `D:\HOSC\validation\` (isolated).
- API keys (`OPENCODE_API_KEY`) are read from the environment at request time,
  never stored, printed, or returned in any manifest/response.

## Troubleshooting

| Symptom | Cause | Fix |
|---|---|---|
| `Graphify unavailable` | `graphify` not on PATH | `uv tool install graphifyy` |
| `OPENCODE_API_KEY missing` | env unset | set key (never commit) |
| `invalid model` | wrong `GRAPHIFY_BRAIN_MODEL` | use `opencode/hy3-free` |
| MCP tests skip | `graphify-mcp` can't launch (missing `pywintypes` / `mcp` extras) | use `ohsc --graphify ...` CLI instead |
| `0 edges but nodes present` | reading `edges` key | Graphify writes `links` — read `links` |

## Files

- `ohsc/gateway.py` — capability manifest generator (stdlib only).
- `ohsc/cli.py` — `ohsc` command (activate / capabilities / status / agents / NL request / `--graphify`).
- `ohsc_launcher.py` — global entry point (puts `D:\HOSC` on `sys.path`).
- `~/.local/bin/ohsc` (+ `ohsc.cmd`) — cross-shell shims.
- `skills/OHSC_AGENT_SKILL.md` — agent-facing operating manual.
