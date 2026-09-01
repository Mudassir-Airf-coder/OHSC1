# OHSC Agent Skill

> Operating manual for external coding/AI agents that want to use the OHSC
> (Hermes Obsidian System Control) capability engine through the **Universal
> Capability Gateway**. This file is the single source of truth for *how to
> drive OHSC* — it does NOT replace internal implementation; it is the
> agent-facing interface layer.

---

## 1. Purpose

OHSC is a modular autonomous multi-agent control plane for an Obsidian vault.
It provides:

- **16 specialized agents** (vault ops, notes, search, linking, templates,
  periodic notes, canvas, dashboard, bulk, and graph intelligence).
- **Graphify** — semantic knowledge-graph extraction over a vault.
- **Graphify Brain** — the LLM backend that powers Graphify's semantic
  extraction. It is wired to the **OpenCode** backend (`opencode/hy3-free`).
- **MCP** — graph-navigation tools exposed via Graphify's own MCP server.
- **Planner / Orchestrator / Reviewer** — request routing, execution, and
  verification.

The **Universal Capability Gateway** lets ANY coding agent activate OHSC with
one command and discover/use its capabilities without knowing OHSC's internal Python.

---

## 2. Activation (ONE command)

```bash
ohsc run
```

This starts an OHSC session and prints a **session token**. Copy the token into
your AI tool if the tool asks for one. Then verify:

```bash
ohsc activate
ohsc capabilities --json
ohsc agents --json
```

`ohsc activate` alone still works for a pure health check without creating a new token.

If activation returns `Status: ACTIVE` (or `DEGRADED` when optional Graphify is missing)
the gateway is ready for vault and agent operations.

---

## 3. Capability Discovery

```bash
ohsc capabilities          # machine-readable manifest (human summary)
ohsc capabilities --json   # full JSON manifest
ohsc status --json         # health checks per component
ohsc agents [--json]       # list the 16 registered agents
ohsc doctor [--json]       # diagnostics
```

---

## 4. Agent Workflow (for any AI tool)

1. Read this skill file.
2. Run `ohsc run` — copy session token if needed.
3. Run `ohsc activate` / `ohsc capabilities --json` / `ohsc agents --json`.
4. Execute tasks via natural language or Graphify flags.
5. Verify results; use `--authorized` for writes.

Examples:

```bash
ohsc "create a note titled Hello with content Hi"
ohsc --dry-run "create a MOC for Python"
ohsc --authorized "create a note titled Plan"
ohsc --graphify build "/path/to/vault"
ohsc --graphify query "what are the main themes?"
ohsc --graphify path --source A --target B
ohsc --graphify analyze
```

---

## 5. Safety Rules

- Never expose API keys (`OPENCODE_API_KEY`) in code, logs, or output.
- Never modify the real vault without explicit authorization (`--authorized`).
- Never delete user data silently.
- Never fabricate graph results.
- Graphify analysis is read-only on the vault; artifacts write under OHSC workspace.

---

## 6. Command Reference

| Command | Purpose |
|---|---|
| `ohsc run` | Start session + print token |
| `ohsc activate` | Gateway activation + status |
| `ohsc capabilities [--json]` | Capability manifest |
| `ohsc status [--json]` | Health checks |
| `ohsc agents [--json]` | List registered agents |
| `ohsc doctor [--json]` | Diagnostics |
| `ohsc "<request>"` | Natural-language task |
| `ohsc --graphify build "<vault>"` | Build knowledge graph |
| `ohsc --graphify query "<q>"` | Semantic query |
| `ohsc --graphify path --source A --target B` | Shortest path |
| `ohsc --graphify explain <node>` | Explain a concept |
| `ohsc --graphify analyze` | Structural report |

Programmatic: `import ohsc; rt = ohsc.build_runtime()`
