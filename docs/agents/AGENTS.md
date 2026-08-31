# OHSC Agent Catalog

The runtime registration in `ohsc/system.py` is the authoritative list. It registers 16 agents. Every entry below is classified by its actual runtime role; specialized agents are dispatched through the Agent Registry.

## Infrastructure / safety agents

### permission_agent
- **Role:** permission/safety infrastructure.
- **Purpose:** participates in authorization decisions for protected operations.
- **Operations:** permission checks used by planning/workflows.
- **Dependencies:** core task/permission contracts.
- **Safety:** destructive operations require explicit authorization.

### snapshot_agent
- **Role:** snapshot infrastructure.
- **Purpose:** provides protected-workflow snapshot behavior.
- **Operations:** snapshot/backup lifecycle exposed by the runtime.
- **Safety:** supports recovery before protected changes.

### transaction_agent
- **Role:** transaction infrastructure.
- **Purpose:** coordinates protected change execution and validation.
- **Operations:** transaction lifecycle used by the runtime.
- **Safety:** works with snapshots/validation instead of bypassing the filesystem safety layer.

### reviewer_agent
- **Role:** post-workflow reviewer.
- **Purpose:** reviews workflow results and reports approval/warnings/failures.
- **Operations:** workflow review.
- **Safety:** does not replace the execution agents; it validates their result.

## Vault and content agents

### vault_agent
- **Role:** vault management.
- **Purpose:** verifies and inspects the configured vault.
- **Operations:** `inspect`, `validate`.
- **Input:** vault root/configuration.
- **Output:** vault status information including Markdown count.
- **Safety:** never silently switches to another vault.

### note_agent
- **Role:** note CRUD.
- **Purpose:** create/read/update/append/rename/delete notes.
- **Operations:** `create`, `read`, `update`, `append`, `rename`, `delete`.
- **Safety:** read is safe; writes require authorization; delete is destructive and explicitly authorized.
- **Path safety:** note paths are resolved through the configured safe-join mechanism.

### search_agent
- **Role:** search/query.
- **Purpose:** search vault content and metadata.
- **Operations:** text, tag, property, and filename search.
- **Input:** query + scope/mode.
- **Output:** matching notes and count.
- **Implementation:** uses the vault index when enabled and a filesystem fallback otherwise.

### folder_agent
- **Role:** folder structure.
- **Purpose:** create/rename folders, move notes, analyze organization, and support organization suggestions.
- **Operations:** `create_folder`, `rename_folder`, `move_note`, `analyze`.
- **Safety:** path operations use the path-safety layer; changes are authorized.

### linking_agent
- **Role:** explicit Obsidian link management.
- **Purpose:** manages structural wikilink relationships.
- **Distinction:** it is separate from Graphify semantic relationships.
- **Safety:** link edits are protected writes.

### metadata_agent
- **Role:** metadata/property management.
- **Purpose:** manages note metadata/properties through the registered workflow interface.
- **Operations:** property/metadata updates.
- **Safety:** writes follow normal authorization/path-safety controls.

### template_agent
- **Role:** template application.
- **Purpose:** applies configured templates to notes.
- **Operations:** `apply_template`.
- **Safety:** template application is a write operation and follows workflow authorization.

### periodic_agent
- **Role:** periodic note generation.
- **Purpose:** creates recurring note types.
- **Operations:** `create_daily`, `create_weekly`, `create_monthly`.
- **Safety:** generated notes are normal vault writes and are subject to authorization.

### canvas_agent
- **Role:** Obsidian Canvas operations.
- **Purpose:** handles Canvas-related vault artifacts exposed by the runtime.
- **Safety:** must remain inside configured allowed roots and follow write authorization.

### dashboard_agent
- **Role:** dashboard/MOC/index generation.
- **Purpose:** builds organization views such as dashboards and maps of content.
- **Operations:** `create_moc`, `create_dashboard`, `create_index`.
- **Safety:** these are vault-writing operations and are authorization-controlled.

### bulk_agent
- **Role:** bulk vault operations.
- **Purpose:** handles multi-item operations exposed by the runtime.
- **Safety:** bulk changes must not bypass path safety, permissions, snapshots, validation, or reviewer controls.

## Graph intelligence

### graphify_agent
- **Role:** graph intelligence.
- **Purpose:** semantic knowledge-graph construction and analysis.
- **Operations:** `build`, `query`, `shortest_path`, `explain`, `analyze`.
- **Backend:** Graphify integration plus Graphify Brain using the existing OpenCode/HY3 configuration.
- **Safety:** read-only against the user's vault by default; Graphify artifacts are written to the OHSC workspace. Explicit Graphify semantic relationships are distinct from editable Obsidian wikilinks.
- **Provenance:** extracted/inferred relationship provenance must remain distinguishable.

## Common execution contract

All workflow-executable agents inherit the common `BaseAgent` scaffolding and return structured `AgentResult` objects. The Agent Registry tracks name, role, enabled state, health, and responsibilities. The registry is the runtime source of truth for what agents exist.

## Adding a new agent

1. Implement a `BaseAgent` subclass.
2. Define an `AgentContract`.
3. Add the agent to `ohsc/system.py` registration.
4. Add tests.
5. Update this catalog and the machine-readable capability manifest.
6. Verify permissions, path safety, failure handling, and reviewer behavior.
