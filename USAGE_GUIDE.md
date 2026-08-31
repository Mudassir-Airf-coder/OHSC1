# OHSC — Usage Guide

OHSC is controlled from the command line. Every request is a
natural-language phrase handled by the Orchestrator.

## Command Syntax

```bash
cd D:\HOSC
python -m ohsc.cli "<request>" [--dry-run] [--authorized] [--no-review] [--json]
python -m ohsc.cli --agents          # list all agents
```

### Flags
- `--dry-run` — preview changes only; nothing is written/deleted.
- `--authorized` — explicitly grant permission for write/destructive ops.
- `--no-review` — skip the Reviewer step (not recommended).
- `--json` — emit raw JSON instead of a human summary.
- `--agents` — print the agent registry.

## Example Requests

| Goal | Command |
|------|---------|
| Create a note | `python -m ohsc.cli "Create a note titled Idea with content Hello world"` |
| Read a note | `python -m ohsc.cli "Read note Idea"` |
| Append | `python -m ohsc.cli "Append to note Idea with content More text"` |
| Update | `python -m ohsc.cli "Update note Idea set content New body"` |
| Rename | `python -m ohsc.cli "Rename note Idea to Renamed"` |
| Search text | `python -m ohsc.cli "Search for Hello"` |
| Search tag | `python -m ohsc.cli "Find notes tagged project"` |
| Create folder | `python -m ohsc.cli "Create folder Projects"` |
| Move note | `python -m ohsc.cli "Move note Idea to Projects"` |
| Orphan analysis | `python -m ohsc.cli "Find orphan notes"` |
| Broken links | `python -m ohsc.cli "Find broken links"` |
| Create MOC | `python -m ohsc.cli "Create a MOC for Python"` |
| Daily note | `python -m ohsc.cli "Create a daily note"` |
| Update metadata | `python -m ohsc.cli "Update metadata of note Idea set status=done"` |
| Bulk (safe) | `python -m ohsc.cli "Move all notes tagged project to Archive" --authorized` |
| Delete (safe) | `python -m ohsc.cli "Delete note Idea" --authorized` |
| Dangerous preview | `python -m ohsc.cli --dry-run "Delete note Idea"` |

## Graphify (Semantic Graph Intelligence)

The `graphify_agent` builds a queryable knowledge graph from the vault and
answers graph questions. It is **READ-ONLY** on the vault — it never edits
notes. Graphify must be installed (`uv tool install "graphifyy[mcp]"`) and an
LLM key (e.g. `GEMINI_API_KEY`) must be available for semantic extraction.

| Task | Command |
|------|---------|
| Analyze the vault as a knowledge graph | `python -m ohsc.cli --authorized "Analyze the knowledge graph of this vault"` |
| Find graph hubs / most connected concepts | `python -m ohsc.cli --authorized "Find graph hubs"` |
| Find communities/clusters | `python -m ohsc.cli --authorized "Analyze communities in my vault"` |
| Shortest conceptual path | `python -m ohsc.cli --authorized --graphify path --source "OHSC" --target "Loop Engineering"` |
| Semantic query | `python -m ohsc.cli --authorized --graphify query "What connects Graph Engineering to Knowledge Graph"` |
| Explain a concept | `python -m ohsc.cli --authorized --graphify explain --node "OHSC"` |

Notes:
- Graphify requests also route automatically from natural language (e.g.
  "find the shortest path between X and Y" → `graphify_agent`).
- EXTRACTED edges (real wikilinks) and INFERRED edges (semantic) are kept
  distinct; inferred relationships are never auto-converted to wikilinks.
- All graph data is written to `D:\HOSC\graphify`, never into the vault.

## Safety Notes

- **Read/search/analyze** are always allowed and never modify the vault.
- **Create/append/update/move/rename** are treated as authorized by an
  explicit user request.
- **Delete / mass operations** require `--authorized`. Without it they are
  blocked (or, with `--dry-run`, only previewed).
- Run `--dry-run` first whenever you are unsure.

## Running Tests

```bash
cd D:\HOSC
python -m pytest tests/ -q
```

Tests use an isolated temporary vault — your real vault is never touched.

## Programmatic Use

```python
from ohsc.system import build_runtime
from ohsc.core.orchestrator import Orchestrator

rt = build_runtime()                 # uses D:\HOSC + D:\Mudassir database
orch = Orchestrator(rt)
result = orch.handle("Find orphan notes")
print(result["status"], result["review"])
```
