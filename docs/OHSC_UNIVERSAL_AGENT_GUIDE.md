# OHSC Universal Agent Guide

How ANY external coding agent (OpenCode, Claude Code, Omni Router, OpenClaw, or
another CLI agent) discovers, activates, and uses OHSC.

## One-command bootstrap

```bash
ohsc activate          # from ANY directory
ohsc capabilities --json
ohsc agents --json
```

That is the entire discover-and-use sequence. `ohsc` resolves `D:\HOSC`
automatically via a shim in `~/.local/bin` (`ohsc` for git-bash,
`ohsc.cmd` for CMD/PowerShell).

## Canonical external-agent workflow

1. Agent discovers OHSC is installed (shim on PATH, or file `D:\HOSC`).
2. Agent reads `skills/OHSC_AGENT_SKILL.md` (the primary contract).
3. Agent reads `capabilities/capabilities.json` (machine-readable manifest).
4. Agent runs `ohsc activate` → expects `Status: ACTIVE`.
5. Agent verifies `ohsc status --json` (all component health checks).
6. Agent discovers agents with `ohsc agents --json`.
7. Agent discovers capabilities with `ohsc capabilities --json`.
8. Agent selects the required capability (e.g. `graphify.query`).
9. Agent executes it:
   - natural language: `ohsc "build a knowledge graph of my vault"`
   - direct: `ohsc --graphify build "<vault>"`
10. Agent verifies the structured result (`status`, `success`, `error`).

## Capability summary

| ID | Agent | Read-only |
|---|---|---|
| `graphify.build_graph` | graphify_agent | yes (vs vault) |
| `graphify.query_graph` | graphify_agent | yes |
| `graphify.shortest_path` | graphify_agent | yes |
| `graphify.explain` | graphify_agent | yes |
| `graphify.analyze` | graphify_agent | yes |
| `obsidian.vault` / `note` / `linking` / `metadata` / `template` / `dashboard` / `bulk` | respective agents | write needs `--authorized` |

## Safety contract

- Real vault: `C:\Users\HAJI LAPTOP G55\Documents\Obsidian Vault` — never
  modified without explicit `--authorized`.
- No API-key value is ever printed/logged/returned. `activate` reports only
  `Key: CONFIGURED` / `NOT CONFIGURED`.
- Every graph result is from real extraction (verified by execution).

See `skills/OHSC_AGENT_SKILL.md` for the full contract and `docs/` for the
architecture, Graphify, integration, and validation reports.
