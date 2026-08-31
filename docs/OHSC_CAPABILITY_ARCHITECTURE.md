# OHSC Capability Architecture

How OHSC exposes its capabilities to external agents through a thin,
machine-readable gateway.

## Layered design

```
External coding agent (OpenCode / Claude Code / Omni Router / OpenClaw)
        │
        │  ohsc activate | capabilities --json | agents --json | "<NL request>"
        ▼
OHSC Capability Gateway  (ohsc/cli.py → ohsc/gateway.py)
        │
        ├─ capability_manifest()      → capabilities/capabilities.json
        ├─ activation_status()        → health checks (no secrets)
        ├─ AgentRegistry              → 16 agents (list_agents / summary)
        ├─ Orchestrator + Planner     → NL routing → WorkflowPlan → Tasks
        └─ integrations/
              ├─ graphify/  (Graphify Brain LLM backend = OpenCode hy3-free)
              └─ (MCP adapter — OPTIONAL, skipped when server unavailable)
```

## Components

| Component | File | Role |
|---|---|---|
| Gateway | `ohsc/gateway.py` | capability manifest, activation status, health |
| CLI | `ohsc/cli.py` | `ohsc` subcommands + NL request path |
| Launcher | `ohsc_launcher.py` | resolves `D:\HOSC`, runs `cli.main` |
| Registry | `ohsc/core/agent_registry.py` | 16 agents, discovery |
| Planner | `ohsc/core/planner.py` | NL intent → plan (graph phrasings → graphify_agent) |
| Orchestrator | `ohsc/core/orchestrator.py` | executes plan, enforces safety |
| Reviewer | `ohsc/core/reviewer.py` | validates results/architecture/safety |
| Graphify integration | `ohsc/integrations/graphify/` | build/query/path/explain/analyze |
| Graphify Brain | `ohsc/integrations/graphify/graphify_brain_*` | LLM backend = OpenCode `hy3-free` |

## Capability manifest schema

`capabilities/capabilities.json` (also `ohsc capabilities --json`):

```jsonc
{
  "ohsc":        { "root": "D:\\HOSC", "version": "1.0" },
  "capability_groups": {
    "graphify": {
      "llm_backend": "opencode",
      "model": "opencode/hy3-free",
      "key_configured": true,            // boolean only — never the value
      "operations": [ { "name","purpose","read_only","requires" } ],
      "mcp_tools": [ ... ]
    }
  },
  "interfaces": { "cli": "...", "mcp": "optional" }
}
```

No secret value is ever present. Only the *name* of env vars and boolean
presence flags.

## Why MCP is optional

`graphify-mcp` requires the `mcp` Python SDK (`pywintypes`/`starlette`/`uvicorn`)
which is not installed on this host. `GraphifyMCPClient.is_available()` performs
a real handshake probe and returns `False` when the server cannot serve, so OHSC
falls back to the fully-validated `graphify` CLI. The gateway NEVER depends on
MCP — CLI alone is sufficient for all capabilities.

## Backend preservation

The production backend `OpenCode` + model `opencode/hy3-free` is unchanged.
Graphify Brain forwards to a local OpenAI-compatible proxy that shells out to
`opencode run -m opencode/hy3-free --format json --pure --auto` via STDIN.
No provider/model config was altered.
