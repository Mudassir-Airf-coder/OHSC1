# OHSC — Hermes Obsidian System Control

**A local multi-agent control plane for Obsidian vaults.**  
Any AI coding tool can activate OHSC, read one skill file, and safely operate your knowledge base — notes, links, search, snapshots, and semantic graphs.

[![Python 3.10+](https://img.shields.io/badge/python-3.10%2B-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
[![Status](https://img.shields.io/badge/status-active-success.svg)](#)

---

## Why OHSC exists

Obsidian vaults grow fast. Notes pile up, links break, structure drifts.

OHSC exists so that **you or any AI agent** can control the vault through a **single, safe interface** instead of ad-hoc scripts and unsafe filesystem access.

It is not an Obsidian plugin UI controller.  
It is a **control plane** over the vault filesystem + knowledge graph layer.

Think of it as:

```text
Any AI tool  →  OHSC skill + CLI  →  safe vault ops + Graphify
```

---

## What you can do

| Capability | Description |
|---|---|
| **Notes & folders** | Create, read, update, organize notes and folders |
| **Search** | Full-text and tag search |
| **Wikilinks** | Link management, orphan / broken-link analysis |
| **Metadata** | Frontmatter / properties |
| **Templates & periodic notes** | Templates, daily / weekly notes |
| **Dashboards / MOCs** | Maps of content and index notes |
| **Canvas & bulk ops** | Canvas support and bulk operations |
| **Graphify** | Build semantic knowledge graphs, query, shortest path, hubs, communities, orphans |
| **Safety** | Path containment, permission classes, snapshots, structured review |
| **AI gateway** | One skill + CLI so Claude Code, OpenCode, Cursor, or any agent can drive OHSC |

---

## Quick start

### Requirements

- Python **3.10+**
- An Obsidian vault path (local folder of Markdown files)
- Optional: Graphify + OpenCode (for semantic graph / Graphify Brain)

### Install

```bash
git clone https://github.com/Mudassir-Airf-coder/OHSC1.git
cd OHSC1
pip install -e .
```

### Configure

```bash
# Linux / macOS
export OHSC_SYSTEM_ROOT="$(pwd)"
export OHSC_VAULT_ROOT="/path/to/your/obsidian/vault"

# Windows PowerShell
$env:OHSC_SYSTEM_ROOT = (Get-Location).Path
$env:OHSC_VAULT_ROOT = "C:\path\to\your/obsidian\vault"
```

Optional secrets (never commit):

```bash
# .env (local only)
OPENCODE_API_KEY=your_key_here
GRAPHIFY_BRAIN_BACKEND=opencode
GRAPHIFY_BRAIN_MODEL=opencode/hy3-free
```

### Run

```bash
ohsc run                 # start session + print session token
ohsc activate            # health / capability status
ohsc agents              # list 16 agents
ohsc capabilities --json # machine-readable manifest
ohsc doctor              # diagnostics
```

### Use from any AI tool

1. Run `ohsc run` and copy the **session token** if the tool asks for one  
2. Point the tool at [`skills/OHSC_AGENT_SKILL.md`](skills/OHSC_AGENT_SKILL.md)  
3. The tool discovers capabilities and drives OHSC via CLI  

```bash
ohsc "create a note titled Hello with content Hi there"
ohsc --dry-run "create a MOC for Python"
ohsc --authorized "create a note titled Plan"
ohsc --graphify build "$OHSC_VAULT_ROOT"
ohsc --graphify analyze
```

---

## How it works (core architecture)

```text
User / AI Agent
      │
      ▼
┌─────────────────────┐
│  CLI / Gateway      │  ohsc run | activate | capabilities | agents
└──────────┬──────────┘
           ▼
┌─────────────────────┐
│  Orchestrator       │  plan → execute → review → memory
└──────────┬──────────┘
           ▼
┌─────────────────────┐
│  Planner            │  natural language → WorkflowPlan
└──────────┬──────────┘
           ▼
┌─────────────────────┐
│  Workflow Engine    │  ordered tasks, auth checks
└──────────┬──────────┘
           ▼
┌─────────────────────┐
│  Agent Registry     │  16 specialized agents
└──────────┬──────────┘
           ▼
   PathSafety + Permissions
           ▼
  Vault filesystem  |  Graphify integration
           ▼
      Reviewer → Memory
```

### Design rules (enforced in code)

- **No giant god-agent** — specialized agents, one responsibility each  
- **No silent failures** — structured `AgentResult` everywhere  
- **No unauthorized writes** — READ / WRITE / DESTRUCTIVE + explicit auth  
- **No path escape** — central `PathSafety` allowed roots  
- **Recoverable** — snapshots / transactions before risky ops  
- **Agent-accessible** — skill + CLI, not internal Python imports required  

---

## Agents (16)

| Agent | Role |
|---|---|
| `permission_agent` | Authorization decisions |
| `snapshot_agent` | Snapshots / rollback points |
| `transaction_agent` | Multi-step transaction + rollback |
| `reviewer_agent` | Structured PASS / FAIL review |
| `vault_agent` | Vault-level operations |
| `note_agent` | Note CRUD |
| `search_agent` | Search queries |
| `folder_agent` | Folder structure |
| `linking_agent` | Wikilinks / orphans |
| `metadata_agent` | Frontmatter / properties |
| `template_agent` | Templates |
| `periodic_agent` | Daily / weekly notes |
| `canvas_agent` | Canvas |
| `dashboard_agent` | MOCs / dashboards |
| `bulk_agent` | Bulk operations |
| `graphify_agent` | Semantic graph intelligence |

---

## Graphify (knowledge graph layer)

OHSC keeps Graphify as a **subsystem**, not a merge into core:

- **Build** semantic graph from vault (read-only on vault)  
- **Query** natural-language questions over the graph  
- **Shortest path** between concepts  
- **Explain** node relationships  
- **Analyze** hubs, communities, orphans  

Artifacts are written under the OHSC workspace (not inside the user vault by default).

Graphify Brain (optional LLM backend) is configured for **OpenCode** (`opencode/hy3-free`), not OpenAI-as-branding. API keys stay in environment variables only.

---

## Project structure

```text
OHSC1/
├── ohsc/                      # Python package
│   ├── core/                  # orchestrator, planner, safety, memory, ...
│   ├── agents/                # 16 specialized agents
│   ├── integrations/graphify/ # Graphify client/runner/brain/MCP
│   ├── cli.py                 # CLI entry
│   ├── gateway.py             # capability gateway
│   ├── config.py              # portable configuration
│   └── system.py              # runtime bootstrap
├── skills/
│   └── OHSC_AGENT_SKILL.md    # agent-facing operating manual
├── capabilities/
│   └── capabilities.json      # machine-readable manifest
├── config/
│   └── ohsc.json              # non-secret settings
├── docs/                      # guides & architecture notes
├── tests/                     # pytest suite
├── scripts/                   # dev helpers
├── ohsc_launcher.py           # console script entry
├── pyproject.toml             # packaging
└── README.md
```

---

## Configuration reference

| Variable | Purpose |
|---|---|
| `OHSC_SYSTEM_ROOT` | Install / workspace root (default: package location) |
| `OHSC_VAULT_ROOT` | Path to Obsidian vault |
| `OPENCODE_API_KEY` | Optional Graphify Brain secret |
| `GRAPHIFY_BRAIN_BACKEND` | Default: `opencode` |
| `GRAPHIFY_BRAIN_MODEL` | Default: `opencode/hy3-free` |

See [`.env.example`](.env.example).

---

## Safety model

1. **PathSafety** — operations only inside allowed roots  
2. **Permissions** — READ / WRITE / DESTRUCTIVE classification  
3. **Authorization** — destructive / write paths need `--authorized`  
4. **Snapshots** — capture before risky changes  
5. **Reviewer** — structured verification of outcomes  

OHSC is designed so an AI agent cannot “wander” the whole disk or silently destroy a vault.

---

## Vision (real product direction)

OHSC is meant to become the **standard local control plane** between:

- human users  
- any AI coding agent  
- an Obsidian knowledge environment  

Target experience:

```text
pip install / one-line install
     → ohsc run
     → token + skill
     → any AI tool understands and controls the vault safely
```

Future (documented, not claimed as done): richer MCP surface, stronger installers, cross-platform polish, and optional higher-level “master generator” tooling around OHSC + Graphify + memory systems.

---

## Documentation

| Doc | Contents |
|---|---|
| [skills/OHSC_AGENT_SKILL.md](skills/OHSC_AGENT_SKILL.md) | **Start here if you are an AI agent** |
| [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) | Core architecture |
| [docs/USAGE.md](docs/USAGE.md) | How to use OHSC day to day |
| [SYSTEM_OVERVIEW.md](SYSTEM_OVERVIEW.md) | System overview from source |
| [USAGE_GUIDE.md](USAGE_GUIDE.md) | Additional usage notes |

---

## Development

```bash
export OHSC_SYSTEM_ROOT="$(pwd)"
export OHSC_VAULT_ROOT="/tmp/ohsc_test_vault"
pip install -e ".[dev]"
python -m pytest
python -m compileall ohsc
```

Core is largely **stdlib-first**. Optional Graphify / OpenCode pieces degrade gracefully when missing.

---

## Status & honesty

| Area | Status |
|---|---|
| Core multi-agent runtime | Implemented |
| CLI + gateway | Implemented |
| Session token (`ohsc run`) | Implemented |
| Portable config | Implemented |
| Packaging (`pip install -e .`) | Implemented |
| Graphify integration | Implemented (optional external binary) |
| Universal one-line cloud installer | Not claimed yet |
| Obsidian desktop app UI control | Not implemented (vault filesystem only) |

---

## License

MIT — see [LICENSE](LICENSE).

---

**OHSC** = Hermes Obsidian System Control.  
Control the vault. Expose the skill. Let any agent work safely.
