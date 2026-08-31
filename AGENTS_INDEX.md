# OHSC — Agents Index

Total agents: 16
Enabled: 16

## Registered Agents

| Agent | Role | Enabled | Healthy | Responsibilities |
|-------|------|---------|---------|------------------|
| permission_agent | permission_intent | True | True | Classify READ/WRITE/DESTRUCTIVE, Enforce auth rules |
| snapshot_agent | backup_snapshot | True | True | Capture affected files, Restore from snapshot |
| transaction_agent | transaction_rollback | True | True | Prepare/snapshot/execute/validate/commit, Rollback on failure |
| reviewer_agent | reviewer | True | True | Review code/agents/fs/tests/docs, Emit structured verdict |
| vault_agent | vault_management | True | True | Verify vault path, Inspect vault structure, Validate vault availability, Never assume the vault exists |
| note_agent | note_crud | True | True | Create, Read, Update, Append, Rename, Delete notes, Enforce authorization for write/destructive ops, Never silently delete notes |
| search_agent | search_query | True | True | Full-text / filename / folder / tag / property / link search, Use index for speed; verify against filesystem |
| folder_agent | folder_structure | True | True | Create/rename folders, Move notes, Analyze organization, Suggest improvements |
| linking_agent | linking_graph | True | True | Create evidence-based wikilinks, Detect broken links, Detect orphan notes and hubs, Analyze graph relationships |
| metadata_agent | properties_metadata | True | True | Read/create/update frontmatter, Normalize metadata, Manage tags, Validate property formats, Preserve unrelated existing metadata |
| template_agent | template | True | True | Discover/validate/create templates, Apply templates to notes |
| periodic_agent | periodic_notes | True | True | Create daily/weekly/monthly notes, Apply templates, Avoid duplicate notes, Detect existing before creation |
| canvas_agent | canvas | True | True | Create/read/modify .canvas files, Validate canvas JSON, Never corrupt existing canvas files |
| dashboard_agent | dashboard_moc | True | True | Create MOCs, indexes, dashboards, Connect related notes, Preserve existing content unless told otherwise |
| bulk_agent | bulk_operations | True | True | Multi-file operations, Preview affected files, Dry-run, Transaction + rollback, Report partial failures |
| graphify_agent | graph_intelligence | True | True | Semantic knowledge-graph analysis (READ-ONLY on vault), Extracted/Inferred edges, Shortest path, Communities, Explanation; delegates to Graphify CLI/MCP, writes only to D:\HOSC\graphify |

## Adding a New Agent

1. Create `ohsc/agents/my_agent.py` subclassing `BaseAgent`.
2. Define `contract = AgentContract(...)` and implement `execute`.
3. Add one `rt.registry.register(MyAgent(rt))` line in `ohsc/system.py`.
4. Add unit/integration tests under `tests/`.

The core architecture is unchanged; only the registry grows.