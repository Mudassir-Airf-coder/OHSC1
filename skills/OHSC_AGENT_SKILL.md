# OHSC Agent Skill

> Operating manual for external coding/AI agents that want to use the OHSC
> (Hermes Obsidian System Control) capability engine through the **Universal
> Capability Gateway**. This file is the single source of truth for *how to
> drive OHSC* — it does NOT replace internal implementation; it is the
> agent-facing interface layer.

---

## 1. Purpose

OHSC is a modular autonomous multi-agent control plane for an Obsidian vault
(located at `C:\Users\HAJI LAPTOP G55\Documents\Obsidian Vault`). It provides:

- **16 specialized agents** (vault ops, notes, search, linking, templates,
  periodic notes, canvas, dashboard, bulk, and graph intelligence).
- **Graphify** — semantic knowledge-graph extraction over a vault.
- **Graphify Brain** — the LLM backend that powers Graphify's semantic
  extraction. It is wired to the **OpenCode** backend (`opencode/hy3-free`).
- **MCP** — graph-navigation tools exposed via Graphify's own MCP server.
- **Planner / Orchestrator / Reviewer** — request routing, execution, and
  verification.

The **Universal Capability Gateway** lets ANY coding agent on this laptop
activate OHSC with one command and discover/use its capabilities without
knowing OHSC's internal Python.

---

## 2. Activation (ONE command)

```bash
ohsc activate
```

This verifies installation, Python, configuration, agent registry, Graphify,
Graphify Brain (OpenCode backend), and required env vars, then prints:

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

The `ohsc` command works from **any directory** (PowerShell/CMD/git-bash).
It resolves `D:\HOSC` automatically via a shim in `~/.local/bin`
(`ohsc` for git-bash, `ohsc.cmd` for CMD/PowerShell).

If activation returns `Status: ACTIVE` the gateway is ready.

---

## 3. Capability Discovery

```bash
ohsc capabilities          # machine-readable manifest (human summary)
ohsc capabilities --json   # full JSON manifest
ohsc status --json         # health checks per component
ohsc agents                # list the 16 registered agents
```

The manifest describes every capability: name, purpose, responsible agent,
required inputs, output format, read-only flag, external-API/LLM requirement.

---

## 4. Agent Architecture

| Component | Responsibility |
|---|---|
| **Planner** | Maps natural-language intent → `WorkflowPlan` of `Task`s. Graph-specific phrasings are routed to `graphify_agent` first (see `INTENT_RULES` in `ohsc/core/planner.py`). |
| **Orchestrator** | Executes the plan against the agent registry; enforces safety/permissions; calls the Reviewer. |
| **Agents** | 16 specialized workers (see §5). |
| **Skills** | Reusable procedural modules under `ohsc/core/skills/`. |
| **Integrations** | External tools — Graphify (knowledge graph), Graphify Brain (LLM). |
| **Reviewer** | Validates results, architecture integrity, safety before returning to the caller. |
| **Graphify** | Builds/queries the semantic knowledge graph. |
| **Graphify Brain** | LLM backend for Graphify's semantic extraction; OpenCode (`opencode/hy3-free`). |

---

## 5. Available Agents (16, all enabled)

| Agent | Role | Capabilities (summary) | Restrictions |
|---|---|---|---|
| `permission_agent` | permission_intent | Authorization decisions | Read-only policy |
| `snapshot_agent` | backup_snapshot | Vault snapshots/rollback points | Read-only capture |
| `transaction_agent` | transaction_rollback | Atomic multi-step rollback | Destructive only when authorized |
| `reviewer_agent` | reviewer | Result/architecture verification | Read-only |
| `vault_agent` | vault_management | Vault-level ops | Write needs authorization |
| `note_agent` | note_crud | Create/read/update/delete notes | Write needs authorization |
| `search_agent` | search_query | Full-text/search queries | Read-only |
| `folder_agent` | folder_structure | Folder create/move | Write needs authorization |
| `linking_agent` | linking_graph | Wikilink edit/repair/orphan analysis | Write needs authorization |
| `metadata_agent` | properties_metadata | Frontmatter/YAML props | Write needs authorization |
| `template_agent` | template | Note templates | Write needs authorization |
| `periodic_agent` | periodic_notes | Daily/weekly notes | Write needs authorization |
| `canvas_agent` | canvas | Canvas boards | Write needs authorization |
| `dashboard_agent` | dashboard_moc | Dashboard/MOC generation | Write needs authorization |
| `bulk_agent` | bulk_operations | Bulk edits | Destructive — authorized only |
| `graphify_agent` | graph_intelligence | Knowledge-graph build/query/path/explain/analyze | Read-only vs vault (writes graph artifacts only under OHSC workspace) |

---

## 6. Graphify Capability

Operations (`graphify_agent` actions → `graphify` CLI):

- **build_graph** — semantic extraction from a vault → `graph.json` + `graph.html` + `GRAPH_REPORT.md`. Read-only against the vault.
- **query_graph** — natural-language question over the built graph (BFS traversal, community-aware).
- **shortest_path** — conceptual shortest path between two concepts (undirected by default).
- **explain** — why/how a concept relates to others (provenance + connections).
- **analyze** — structural report: hubs (god-nodes), communities, orphans, stats.

Graph artifacts:
- `graph.json` — networkx node_link format. **Edges are stored under the `links` key** (not `edges`); nodes under `nodes`; communities per-node via the `community` attribute; hyperedges under `hyperedges`.
- `graph.html` — interactive HTML visualization.
- `GRAPH_REPORT.md` — human-readable report.

Provenance: every edge carries `confidence` (`EXTRACTED` = explicit, e.g. a real wikilink; `INFERRED` = semantic, discovered by the model). OHSC preserves this distinction and never presents an INFERRED link as a fact.

---

## 7. Graphify Brain

- **What it does:** provides the LLM that powers Graphify's semantic extraction
  (turning note text into nodes/edges/hyperedges).
- **Why it exists:** Graphify needs an LLM to extract meaning beyond syntax;
  Graphify Brain abstracts the provider so OHSC controls config centrally.
- **Communication with Graphify:** Graphify is invoked with
  `OPENAI_BASE_URL` / `OPENAI_MODEL` / `OPENAI_API_KEY` pointing at a local
  OpenAI-compatible **proxy** (`GraphifyBrainProxy`). The proxy forwards to
  the configured Brain LLM.
- **LLM backend:** **OpenCode** (`opencode run` CLI, model `opencode/hy3-free`).
- **OpenCode backend:** `GraphifyBrainLLM` → `OpenCodeBrainBackend` shells out to
  `opencode run -m opencode/hy3-free --format json --pure --auto`, piping the
  prompt via **STDIN** (Windows command-line length limit makes argv passing
  unreliable for large prompts).
- **Model configuration (env):**
  - `GRAPHIFY_BRAIN_BACKEND=opencode`
  - `GRAPHIFY_BRAIN_MODEL=opencode/hy3-free`
  - `OPENCODE_API_KEY` — required, externally configured (never hard-coded).
- **Failure behavior:** empty/filtered model response → graphify reports
  "LLM returned empty or filtered response"; the proxy surfaces a clean
  `brain_error` (never leaks key details).
- **Caching:** Graphify caches per-chunk semantic results; re-running on an
  unchanged vault is fast. OHSC's `GraphifyRunner` also tracks vault mtime +
  graph version and reuses a built graph when valid.
- **Performance (measured, OpenCode CLI):** basic vault 57.6s, intermediate
  76.4s, advanced 84.1s (per full build; ~20s is the per-call `opencode run`
  spawn overhead).

---

## 8. OpenCode Backend

Configuration (names are the ACTUAL env vars; values are placeholders):

```
OPENCODE_API_KEY=<secret — externally configured, never printed>
GRAPHIFY_BRAIN_BACKEND=opencode
GRAPHIFY_BRAIN_MODEL=opencode/hy3-free
```

**NEVER expose the API key.** The proxy validates presence and ignores the
value. Debug dumps (env `GRAPHIFY_BRAIN_DEBUG=<path>`) capture prompt/response
shape only — no secrets, no key material.

`opencode run` is invoked (not `opencode serve`, which is billing-blocked on
this host for the hosted workspace). The CLI path executes `opencode/hy3-free`
directly and is the production transport.

---

## 9. MCP

Graphify ships an MCP server (`graphify-mcp` / `python -m graphify.serve
graph.json`) exposing graph-navigation tools. OHSC's `GraphifyMCPClient`
(`ohsc/integrations/graphify/graphify_mcp.py`) speaks to it over stdio.

Relevant tools (codespace-scoped; PR tools excluded):

| Tool | Purpose | Inputs | Output |
|---|---|---|---|
| `query_graph` | Semantic question over graph | `query` | answer text |
| `get_node` | Fetch a node by id/label | `node` | node + connections |
| `get_neighbors` | Neighbors of a node | `node` | neighbor list |
| `god_nodes` | Most-connected hubs | — | ranked hubs |
| `graph_stats` | Node/edge/community counts | — | stats |
| `shortest_path` | Path between two concepts | `source`,`target`,`undirected` | path |
| `get_community` | Nodes in a community | `community` | node list |

> NOTE: the OHSC MCP adapter is a thin stdio client; the `graphify` CLI
> (`ohsc --graphify ...`) is the primary, fully-validated interface and is
> preferred for agent use.

---

## 10. Vault Operations & Safety

- **Authorized vault:** `C:\Users\HAJI LAPTOP G55\Documents\Obsidian Vault`.
- **Read-only Graphify analysis:** Graphify extraction reads the vault and
  writes artifacts ONLY under the OHSC workspace (`D:\HOSC\graphify\graphs\`),
  never inside the user's vault.
- **The REAL vault must NEVER be modified by Graphify analysis** unless a
  future task explicitly authorizes it.
- **Temporary testing** happens in `D:\HOSC\validation\<vault>\` — isolated
  from the real vault.
- **Safety mode:** OHSC config `safety_mode: strict`. Write/destructive ops
  require explicit authorization (`--authorized`).

---

## 11. Agent Workflow

1. `ohsc activate` — confirm gateway is ACTIVE.
2. `ohsc capabilities` — discover what is available.
3. Identify the required capability (e.g. graphify for graph tasks).
4. Call the capability — either:
   - natural language: `ohsc "find the shortest path between X and Y"`
   - direct: `ohsc --graphify path --source X --target Y`
5. Use the returned information (graph path, answer, stats).
6. For vault mutations, ensure authorization and let the Reviewer validate.
7. Report results with provenance (EXTRACTED vs INFERRED edges).

---

## 12. Example Tasks (Quick Map)

- "Analyze this vault." → `ohsc --graphify build "<vault>"` (or NL).
- "Find relationships between these notes." → `ohsc --graphify query "..."`.
- "Build a knowledge graph." → `ohsc --graphify build`.
- "Find the shortest path between two concepts." → `ohsc --graphify path --source A --target B`.
- "Identify orphan notes." → `ohsc --graphify analyze` (orphans in report).
- "Find major hubs." → `ohsc --graphify analyze` (god-nodes).
- "Analyze this project's knowledge structure." → `ohsc --graphify analyze`.
- "Use Graphify to understand the relationship between these concepts." → `ohsc --graphify explain <concept>`.

---

## 12b. PROJECT CREATION (vault / knowledge base / MOC)

OHSC can *create* structure, not just analyze it. This requires write
authorization (`--authorized`). All writes go to the **authorized vault** only.

| Goal | Command |
|---|---|
| Create an Obsidian vault skeleton | `ohsc "create a vault at <path>" --authorized` |
| Create a note | `ohsc "create a note titled <T> with content <C>" --authorized` |
| Create a knowledge base from a repo | `ohsc "build a knowledge vault for this project" --authorized` |
| Related-note structure / wikilinks | `ohsc "link related notes about <topic>" --authorized` |
| MOC / dashboard | `ohsc "create a MOC for <topic>" --authorized` |
| Research structure | `ohsc "set up a research vault with daily notes and a MOC" --authorized` |

> The natural-language Orchestrator routes these to the correct agent
> (`vault_agent`, `note_agent`, `linking_agent`, `dashboard_agent`, …).
> Graphify is READ-ONLY against the vault; it never creates notes. Use Graphify
> to *analyze* what you built, then let the note/linking agents *organize* it.

---

## 12c. EXAMPLE WORKFLOWS (A–H, using the real interface)

**A. Create a basic knowledge vault**
```
ohsc activate
ohsc "create a vault at D:\projects\kb" --authorized
ohsc "create a note titled Welcome with content '# Welcome'"
ohsc --graphify build "D:\projects\kb"     # verify structure as a graph
```

**B. Intermediate project knowledge graph**
```
ohsc --graphify build "<project-dir>"      # semantic extraction (read-only)
ohsc --graphify analyze                     # hubs / communities / orphans
ohsc --graphify query "what does this project depend on?"
```

**C. Advanced research graph**
```
ohsc --graphify build "<research-vault>"
ohsc --graphify explain "topic-X"           # provenance + connections
ohsc --graphify path --source "paper-A" --target "method-B"
ohsc "create a MOC linking the main themes" --authorized
```

**D. Analyze an existing vault**
```
ohsc --graphify build "C:\Users\HAJI LAPTOP G55\Documents\Obsidian Vault"
ohsc --graphify analyze
```

**E. Relationship between two notes**
```
ohsc --graphify query "how are <Note A> and <Note B> related?"
```

**F. Shortest path between two concepts**
```
ohsc --graphify path --source "OpenCode" --target "Graphify"
```

**G. Create a MOC**
```
ohsc "create a MOC for Python tooling" --authorized
```

**H. Update an existing project vault**
```
ohsc --graphify build "<existing-vault>"    # inspect current structure
ohsc "add a note titled Changelog summarizing v2" --authorized
ohsc "link Changelog to the relevant notes" --authorized
ohsc --graphify build "<existing-vault>"    # re-verify
```

> In every workflow: activate → discover (`capabilities`) → route → execute →
> validate (`ohsc status`, Reviewer). Never skip the activation/status check.

---

## 12d. OUTPUT CONTRACT

Each capability returns a structured result. The gateway/CLI JSON shape:

```jsonc
{
  "status": "SUCCESS | FAIL | DEGRADED",
  "success": true,                  // bool
  "agent": "graphify_agent",        // responsible agent
  "operation": "shortest_path",     // capability name
  "result": { "answer": "...", "graph_path": "..." },
  "error": null,                    // string when !success
  "retryable": true                 // whether a retry may help
}
```

- `ohsc status --json` / `ohsc capabilities --json` return the manifest/health
  dicts shown in §3. No secret value ever appears — only env-var *names* and
  boolean presence flags (`key_present`).
- On failure, `error` carries a human-readable cause; `retryable` tells the
  agent whether to retry (e.g. transient timeout) or fix config first.

---

## 13. Safety Rules

- Never expose API keys (OPENCODE_API_KEY) in code, logs, reports, or output.
- Never modify the real vault without explicit authorization.
- Never delete user data.
- Never silently change configuration.
- Never fabricate graph results — every node/edge must come from real
  extraction (verified by execution).
- Never claim a capability succeeded without execution evidence.
- Use temporary vaults (`D:\HOSC\validation\`) for testing.

---

## 14. Troubleshooting

| Symptom | Cause | Fix |
|---|---|---|
| `Graphify unavailable` | `graphify` not on PATH | Install via `uv tool install graphifyy` |
| `OpenCode unavailable` | `opencode` CLI missing | Install OpenCode; verify `where opencode` |
| `API key missing` | `OPENCODE_API_KEY` unset | Set the key in environment/config (never commit) |
| `invalid model` | `GRAPHIFY_BRAIN_MODEL` wrong | Use `opencode/hy3-free` |
| `rate limit` | OpenCode throttling | Retry; reduce `--max-concurrency` |
| `timeout` | Large vault / slow model | Increase timeout; shrink token budget |
| `corrupted graph` | Partial write | Re-run `ohsc --graphify build` (force) |
| `MCP unavailable` | `graphify-mcp` not running | Use `ohsc --graphify ...` CLI instead |
| `vault path mismatch` | Wrong vault_root | Check `OHSC_SYSTEM_ROOT` / config |
| `invalid capability` | Unknown subcommand | `ohsc capabilities` to list |
| `empty extraction` | Prompt truncated (argv) | Fixed: backend uses STDIN transport |
| `0 edges but nodes present` | Reading `edges` key | graphify writes `links` — read `links` |

---

## 15. Command Reference

| Command | Purpose |
|---|---|
| `ohsc activate` | Gateway activation + status |
| `ohsc capabilities [--json]` | Capability manifest |
| `ohsc status [--json]` | Health checks |
| `ohsc agents` | List registered agents |
| `ohsc "<request>"` | Natural-language task (routed by Planner) |
| `ohsc --graphify build "<vault>"` | Build knowledge graph |
| `ohsc --graphify query "<q>"` | Semantic query |
| `ohsc --graphify path --source A --target B` | Shortest path |
| `ohsc --graphify explain <node>` | Explain a concept |
| `ohsc --graphify analyze` | Structural report |

Programmatic: `import ohsc; rt = ohsc.build_runtime()` then use
`rt.registry`, `rt.workflow`, or the Graphify integration modules directly.
