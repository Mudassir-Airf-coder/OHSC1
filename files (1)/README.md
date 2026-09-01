# OHSC — Hermes Obsidian System Control

OHSC is a modular, multi-agent control plane for an Obsidian vault. It
turns natural-language requests ("create a daily note", "find orphan
notes", "build a knowledge graph of this vault") into structured,
authorized, auditable operations against your vault's Markdown files —
and exposes the same capabilities to external coding/AI agents through a
Universal Capability Gateway.

> **Status:** actively developed, stdlib-first, no known secret leaks.
> See `docs/PROJECT_STATUS.md` for a subsystem-by-subsystem verification
> table and `docs/GAPS.md` for known limitations (most importantly:
> current default paths are Windows-only — see "Cross-platform note"
> below).

## Why it exists

Obsidian vaults grow organically. OHSC exists to safely automate the
repetitive parts of vault maintenance — note creation, linking,
metadata, dashboards, periodic notes, bulk operations, and semantic
graph analysis — without a human (or an AI agent acting on their
behalf) ever needing to hand-write unsafe filesystem code, and without
silently making destructive changes.

## What it can do

- **Note operations** — create, read, update, append, rename, delete
  (delete requires explicit authorization).
- **Search** — full-text and tag search over the vault.
- **Linking** — wikilink management, orphan/broken-link detection.
- **Folders** — create/move notes and folders.
- **Templates & metadata** — apply templates, read/write frontmatter
  properties.
- **Periodic notes** — daily/weekly/monthly note creation.
- **Dashboards** — MOCs (Maps of Content) and index notes.
- **Canvas & bulk** — Canvas file support, bulk operations across many
  notes.
- **Graphify** — semantic knowledge-graph extraction, querying,
  shortest-path/community/hub analysis over the vault (read-only on the
  vault itself; writes graph artifacts to the OHSC workspace, never into
  the vault). See `docs/GRAPHIFY_INTEGRATION.md`.
- **External-agent gateway** — any coding/AI agent can activate OHSC,
  discover its capabilities/agents, and run operations against a stable,
  structured contract. See `skills/OHSC_AGENT_SKILL.md`.

## Architecture

```
User / External AI Agent
   ↓  CLI (ohsc/cli.py)  or  Gateway (ohsc/gateway.py)
   ↓
Orchestrator            (ohsc/core/orchestrator.py)
   ↓
Planner                 (ohsc/core/planner.py)         — NL request → structured WorkflowPlan
   ↓
Workflow Engine         (ohsc/core/workflow_engine.py) — dependency-ordered task execution
   ↓
Agent Registry          (ohsc/core/agent_registry.py)  — dispatches Task → specific agent
   ↓
Specialized Agents      (ohsc/agents/*.py)             — 12 agents, one responsibility each
   ↓
Filesystem Backend      (ohsc/core/filesystem.py)      — all disk I/O passes through PathSafety
   ↓
Reviewer                (ohsc/core/reviewer.py)        — mandatory structured PASS/FAIL verdict
   ↓
Memory                  (ohsc/core/memory.py)          — records successful request patterns
```

Every step is backed by:

- **`PathSafety`** (`ohsc/core/path_safety.py`) — no agent may touch a
  path outside the configured allowed roots; traversal is rejected.
- **`PermissionAgent`** (`ohsc/core/permissions.py`) — classifies every
  operation as READ / WRITE / DESTRUCTIVE; destructive operations
  require explicit authorization.
- **`SnapshotAgent`** + **`TransactionAgent`** — capture affected files
  before risky operations and support Prepare → Snapshot → Execute →
  Validate → Commit, with honest (non-guaranteed) rollback reporting.
- **Structured contracts** (`ohsc/core/contracts.py`) — agents never
  communicate in free text; every result is a typed `AgentResult` with
  status, data, errors, warnings.

This architecture was verified against the actual source in this pass —
see `docs/PROJECT_STATUS.md` for what was confirmed and how.

## Requirements

- Python 3.10+ (developed/tested against 3.12.3 in this audit).
- The core system (`ohsc/core/`, agents, planner, orchestrator) is
  **standard-library only** — no third-party runtime dependencies.
- Optional: the `graphify` PyPI package (and its `graphify-mcp`
  executable) for Graphify semantic-graph features, plus an LLM backend
  for Graphify Brain (configured via environment variable, no keys are
  committed to this repo).
- Optional: `pytest` to run the test suite.

## Installation

There is currently **no packaging metadata** (`pyproject.toml`/
`setup.py`) in this repository, so OHSC is not yet `pip install`-able —
see `docs/installation/INSTALLATION_READINESS.md` for the full audit.
Today, installation means:

```bash
git clone <this-repo-url>
cd OHSC1
# optional, for the test suite:
pip install pytest --break-system-packages
```

### Cross-platform note

The default system/vault roots in `ohsc/config.py` are currently
hardcoded to a specific Windows layout (`D:\HOSC`, `D:\Mudassir
database`). **Override them** before running on any other machine or OS:

```bash
export OHSC_SYSTEM_ROOT=/path/to/ohsc-workspace
export OHSC_VAULT_ROOT=/path/to/your/obsidian/vault
```

or edit `config/ohsc.json`. This is a known, tracked gap — see
`docs/GAPS.md` (GAP-001) — not a hidden limitation.

## CLI usage

```bash
# Natural-language request
python -m ohsc.cli "Create a note titled Hello with content Hi there"

# Preview only, no changes written
python -m ohsc.cli --dry-run "Create a MOC for Python"

# Explicitly authorize a write/destructive operation
python -m ohsc.cli --authorized "Delete the note Draft"

# Gateway / introspection commands
python -m ohsc.cli activate
python -m ohsc.cli capabilities --json
python -m ohsc.cli agents --json

# Direct Graphify mode
python -m ohsc.cli --graphify build
python -m ohsc.cli --graphify query "How does Planner relate to Orchestrator?"
python -m ohsc.cli --graphify path --source "Planner" --target "Reviewer"
```

## MCP

Graphify includes an MCP adapter (`ohsc/integrations/graphify/graphify_mcp.py`)
exposing graph-navigation tools. There is no separate, standalone
OHSC-level MCP server outside of this Graphify adapter today. Full
breakdown in `docs/integrations/MCP.md`.

## External AI-agent integration

`ohsc/gateway.py` and `ohsc/capabilities.json` implement a discovery/
activation contract so another coding agent can: activate OHSC, list
capabilities and agents (JSON output supported), submit requests, and
receive structured results/errors. The canonical operating manual for
another AI agent is **`skills/OHSC_AGENT_SKILL.md`** — read that first
if you are an AI agent trying to use OHSC.

## Testing

```bash
export OHSC_SYSTEM_ROOT=/tmp/ohsc_test_root
export OHSC_VAULT_ROOT=/tmp/ohsc_test_vault
python -m pytest
```

As of this audit: **61 passed, 10 failed, 11 skipped** on Linux. All 10
failures share one root cause — the Windows-only hardcoded paths
described above (`docs/GAPS.md` GAP-001) — not independent bugs. Tests
use isolated fixture vaults (`tests/graphify_brain_validation/`,
`tests/fixtures/`) rather than a real vault.

## Security

See `SECURITY.md`. Short version: path traversal is blocked centrally,
destructive operations require explicit authorization, no secrets are
committed to this repository (verified by scan), and snapshots exist
for recoverability before risky operations.

## Project structure

```
OHSC1/
├── ohsc/                    # the package
│   ├── core/                # orchestrator, planner, workflow engine, safety, memory, index
│   ├── agents/               # 12 specialized agents
│   ├── integrations/graphify/  # Graphify client/runner/MCP/brain
│   ├── skills/                # runtime skill registry
│   ├── cli.py / gateway.py / config.py / system.py
├── tests/                   # pytest suite + synthetic fixture vaults
├── docs/                    # architecture, installation, integrations, agents, status, gaps
├── skills/OHSC_AGENT_SKILL.md  # operating manual for external AI agents
├── capabilities/ , ohsc/capabilities.json  # machine-readable capability manifest (see GAP-003)
├── config/ohsc.json          # configuration
├── scripts/                  # test/report generation utilities
└── snapshots/, index/, memory/  # runtime data directories
```

## Development

See `CONTRIBUTING.md` for how to add an agent, a skill, or an
integration, and coding/documentation conventions.

## Roadmap

Documented separately as explicitly-future, not-yet-implemented work:
see `docs/architecture/FUTURE_MASTER_MCP_GENERATOR.md`.

## Troubleshooting

- **`ohsc activate` reports `DEGRADED`** — usually means the optional
  `graphify`/`graphify-mcp` binaries aren't installed or an LLM backend
  key isn't set. This is expected, graceful behavior, not a crash.
- **Tests fail with paths like `.../D:\HOSC/...`** — you're hitting
  GAP-001; set `OHSC_SYSTEM_ROOT`/`OHSC_VAULT_ROOT` before running.
- **Path errors when running outside the repo directory** — there's no
  installed package yet (see Installation above); run from the repo
  root.
