# OHSC — Obsidian System Control

**A local multi-agent control plane for Obsidian vaults**

OHSC turns your Obsidian vault into a **safe, structured, agent-controllable interface** instead of ad-hoc scripts and unsafe filesystem access.

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

### Install (one command — recommended)

```bash
git clone https://github.com/Mudassir-Airf-coder/OHSC1.git
cd OHSC1

# Linux / macOS
bash setup.sh

# Windows PowerShell
.\setup.ps1
```

`setup.sh` / `setup.ps1` will:
1. Detect `python3` (or `python` fallback)
2. `pip install -e .` so the `ohsc` command is available
3. Install `uv` if missing
4. Install Graphify CLI: `uv tool install "graphifyy[mcp,openai]"`
5. Create `.env` from `.env.example` and optionally prompt for `GROQ_API_KEY`
6. Run `ohsc doctor` for a health check

Unattended / CI: `bash setup.sh --unattended`

### Configure

```bash
# Linux / macOS
export OHSC_SYSTEM_ROOT="$(pwd)"
export OHSC_VAULT_ROOT="/path/to/your/obsidian/vault"

# Windows PowerShell
$env:OHSC_SYSTEM_ROOT = (Get-Location).Path
$env:OHSC_VAULT_ROOT = "C:\path\to\your\obsidian\vault"
```

Secrets live in `.env` (never commit). Recommended defaults:

```bash
GRAPHIFY_BRAIN_BACKEND=groq
GRAPHIFY_BRAIN_MODEL=openai/gpt-oss-120b
GROQ_API_KEY=your_groq_key_here
```

Only `GROQ_API_KEY` is required for Graphify. OHSC automatically maps it to the
`OPENAI_*` variables the external `graphify` CLI expects — no manual export needed.

### Run

```bash
ohsc run                 # start session + print session token
ohsc activate            # health / capability status
ohsc agents              # list 16 agents
ohsc capabilities --json # machine-readable manifest
ohsc doctor              # environment / dependency diagnostics
ohsc --graphify build "$OHSC_VAULT_ROOT"
```

### Use from any AI tool

1. Run `ohsc run` and copy the **session token** if the tool asks for one  
2. Point the tool at `skills/OHSC_AGENT_SKILL.md`  
3. Ask it to operate the vault through OHSC only (never raw filesystem writes)

---

## Architecture (high level)

```text
┌─────────────────────────────────────────────────────────────┐
│  Any AI tool / agent (Claude Code, OpenCode, Cursor, …)    │
└──────────────────────────┬──────────────────────────────────┘
                           │  skill.md + CLI / session token
┌──────────────────────────▼──────────────────────────────────┐
│  OHSC CLI / Gateway                                         │
│  ohsc run | activate | doctor | natural-language tasks      │
└──────────────────────────┬──────────────────────────────────┘
                           │
┌──────────────────────────▼──────────────────────────────────┐
│  Orchestrator → Planner → Workflow Engine → Reviewer        │
└──────────────────────────┬──────────────────────────────────┘
                           │
        ┌──────────────────┼──────────────────┐
        ▼                  ▼                  ▼
   16 domain agents   PathSafety +       Graphify client
   (note, search,     permissions +      (extract / query /
    folder, …)        snapshots          path / explain)
```

See [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) for details.

---

## Graphify

Graphify turns a folder of notes (and mixed content) into a queryable semantic graph.

```bash
ohsc --graphify build "$OHSC_VAULT_ROOT"
ohsc --graphify query "What connects X and Y?"
ohsc --graphify path "Concept A" "Concept B"
```

Requires:
- `GROQ_API_KEY` (or another configured OpenAI-compatible backend)
- Graphify CLI installed via setup (`uv tool install "graphifyy[mcp,openai]"`)

OHSC injects `OPENAI_API_KEY` / `OPENAI_BASE_URL` / `OPENAI_MODEL` into the Graphify subprocess automatically when `GRAPHIFY_BRAIN_BACKEND` is `groq`, `openrouter`, or `openai`.

---

## Safety model

| Layer | Role |
|---|---|
| **PathSafety** | All paths must stay inside `OHSC_VAULT_ROOT` |
| **Permissions** | READ / WRITE / DESTRUCTIVE classes |
| **Snapshots** | Pre-change recovery points |
| **Reviewer** | Structured review before destructive work |
| **Transaction** | Grouped ops with rollback support |

Agents never bypass these layers.

---

## Honesty table

| Area | Status |
|---|---|
| Core 16 agents + orchestrator | Implemented |
| PathSafety / permissions / snapshots | Implemented |
| Graphify client + optional Brain | Implemented |
| Packaging (`pip install -e .`) | Implemented |
| One-command setup (`setup.sh` / `setup.ps1`) | Implemented |
| Cross-platform Python detection | Implemented |
| Auto-map GROQ → OPENAI_* for Graphify CLI | Implemented |
| Universal skill for external AI tools | Implemented (`skills/OHSC_AGENT_SKILL.md`) |
| Obsidian plugin UI | Not in scope |
| Cloud multi-user SaaS | Not in scope |

---

## Development

```bash
python3 -m pip install -e ".[dev]"
python3 -m pytest
```

---

## License

MIT — see [LICENSE](LICENSE).
