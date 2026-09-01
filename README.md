# OHSC — Hermes Obsidian System Control

**OHSC** is a modular multi-agent control plane for an Obsidian vault. It turns natural-language requests into structured, authorized, auditable operations against your vault — and exposes the same capabilities to any external AI coding agent through a Universal Capability Gateway.

> Status: actively developed · stdlib-first core · Graphify integration · agent-accessible

---

## What OHSC does

| Area | Capability |
|------|------------|
| **Vault control** | Create / read / update notes, folders, metadata, templates, periodic notes |
| **Search & links** | Full-text / tag search, wikilinks, orphan & broken-link detection |
| **Dashboards** | MOCs, index notes, Canvas support, bulk operations |
| **Graphify** | Semantic knowledge-graph build, query, shortest path, hubs, communities, orphans |
| **Safety** | Path containment, READ/WRITE/DESTRUCTIVE permissions, snapshots, reviewer |
| **AI agents** | One skill file + CLI so any coding agent can discover and drive OHSC |

---

## Quick start

### 1. Install (local / development)

```bash
# From the repository root
pip install -e .

# Or without packaging (dev):
export OHSC_SYSTEM_ROOT="$(pwd)"   # Linux/macOS
# PowerShell: $env:OHSC_SYSTEM_ROOT = (Get-Location).Path
```

### 2. Configure vault

```bash
export OHSC_VAULT_ROOT="/path/to/your/obsidian/vault"
```

### 3. Activate / run

```bash
ohsc activate          # health + capability check
ohsc run               # start session (prints a session token)
ohsc status
ohsc agents
ohsc capabilities --json
```

### 4. Use from any AI tool

1. Run `ohsc run` — copy the printed **session token**
2. Point the AI tool at `skills/OHSC_AGENT_SKILL.md`
3. The tool reads the skill, understands capabilities, and drives OHSC via CLI

---

## CLI (high level)

```text
ohsc activate              Gateway activation + status
ohsc run                   Start session and print session token
ohsc status [--json]       Health checks
ohsc capabilities [--json] Machine-readable capability manifest
ohsc agents [--json]       List registered agents
ohsc doctor [--json]       Diagnostics
ohsc "create a note ..."   Natural-language request
ohsc --graphify build <vault>
ohsc --dry-run "..."
ohsc --authorized "..."    Allow write / destructive ops
```

---

## Architecture (simplified)

```text
User / AI Agent
      │
      ▼
 CLI / Gateway
      │
      ▼
 Orchestrator
      │
      ├─► Planner          (NL → structured WorkflowPlan)
      ├─► Workflow Engine  (ordered task execution)
      ├─► Agent Registry   (16 specialized agents)
      ├─► PathSafety + Permissions
      ├─► Graphify integration
      └─► Reviewer → Memory
```

Core code lives under `ohsc/`. The implementation is the source of truth.

---

## Configuration

| Variable | Purpose |
|----------|---------|
| `OHSC_SYSTEM_ROOT` | Install / workspace root (default: package location) |
| `OHSC_VAULT_ROOT` | Obsidian vault path |
| `OPENCODE_API_KEY` | Optional — Graphify Brain (OpenCode backend) |
| `GRAPHIFY_BRAIN_BACKEND` | Default: `opencode` |
| `GRAPHIFY_BRAIN_MODEL` | Default: `opencode/hy3-free` |

Secrets never belong in the repo. Use `.env` locally (see `.env.example`).

---

## Safety

- All filesystem access goes through **PathSafety** (allowed roots only)
- Operations classified **READ / WRITE / DESTRUCTIVE**
- Destructive ops require explicit authorization (`--authorized`)
- Snapshots before risky changes
- Reviewer produces structured PASS / FAIL verdicts

---

## Project layout

```text
ohsc/                 # Python package (core, agents, integrations, CLI, gateway)
skills/               # Agent-facing skill (OHSC_AGENT_SKILL.md)
capabilities/         # Machine-readable capability manifest
config/               # ohsc.json configuration
tests/                # pytest suite + fixtures
docs/                 # Architecture & integration notes
scripts/              # Dev / validation helpers
ohsc_launcher.py      # Console entry point
pyproject.toml        # Packaging
```

---

## Testing

```bash
export OHSC_SYSTEM_ROOT="$(pwd)"
export OHSC_VAULT_ROOT="/tmp/ohsc_test_vault"
python -m pytest
```

---

## License

See [LICENSE](LICENSE).
