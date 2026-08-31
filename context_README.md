# OHSC — Full Context Report (Hermes Obsidian System Control)

**Generated:** 2026-08-31 | **Version:** 1.0.0 | **Language:** Python 3.11 (stdlib only)

---

## 1. Project Identity

| Field | Value |
|---|---|
| **Full Name** | Hermes Obsidian System Control |
| **Short Name** | OHSC |
| **System Folder** | `D:\HOSC` |
| **Obsidian Vault** | `D:\Mudassir database` (default), configurable via `config/ohsc.json` |
| **Python** | 3.11, **zero external dependencies** |
| **Entry Point** | `ohsc_launcher.py` → `ohsc/cli.py` |

OHSC is **not** a single script. It is a **control plane**: a coordinator (Orchestrator) that receives natural-language requests, asks a Planner to break them into a structured execution plan, runs that plan through a Workflow Engine across **16 specialized agents**, validates every step, and sends the result to an independent **Reviewer** before declaring success.

---

## 2. Architecture (High-Level)

```
USER → Orchestrator → Planner → WorkflowEngine → Specialized Agents
                            ↓                          ↓
                        Reviewer ←──────────────  Validation / Logs
```

**Core pipeline:**
1. `Orchestrator.handle(request)` — receives natural-language input
2. `Planner.plan(request)` — converts NL → `WorkflowPlan` (list of `Task` objects with agent, action, params, op_class)
3. `WorkflowEngine.run(plan)` — dispatches each Task to its registered agent (sequential with dependency ordering)
4. Each agent: `PathSafety.validate` → `execute` → `AgentResult` (+ audit log via `record_event`)
5. `ReviewerAgent.review_workflow(report)` → structured PASS/FAIL + required fixes
6. `Memory` records successful request patterns
7. User-friendly final result returned

---

## 3. Project File Structure

```
D:\HOSC\
├── ohsc/                          # Main package
│   ├── __init__.py
│   ├── cli.py                     # CLI entry point
│   ├── config.py                  # Centralized SystemConfig
│   ├── gateway.py                 # Universal Capability Gateway
│   ├── system.py                  # Bootstrap: register all agents
│   ├── core/                      # Core infrastructure
│   │   ├── agent_base.py          # BaseAgent + AgentContract imports
│   │   ├── agent_registry.py      # BaseAgent ABC, AgentContract, AgentRegistry
│   │   ├── contracts.py           # Task, AgentResult, OpClass, TaskStatus
│   │   ├── exceptions.py          # Exception hierarchy
│   │   ├── path_safety.py         # Centralized allowed-root validation
│   │   ├── permissions.py         # READ/WRITE/DESTRUCTIVE classification
│   │   ├── filesystem.py          # VaultBackend ABC + FilesystemBackend
│   │   ├── logging.py             # Rotating logs + audit trail
│   │   ├── validation.py          # Input/contract validation
│   │   ├── snapshot_agent.py      # Capture/restore file snapshots
│   │   ├── transaction_agent.py   # PREPARE→SNAPSHOT→EXECUTE→VALIDATE→COMMIT
│   │   ├── indexing.py            # Frontmatter/wikilink/tag parsing
│   │   ├── index_store.py         # Incremental vault index with persistence
│   │   ├── memory.py              # System/agent/workflow/history memory
│   │   ├── runtime.py             # Bootstraps all shared infrastructure
│   │   ├── planner.py             # NL → structured plan + param extraction
│   │   ├── workflow_engine.py     # Sequential/parallel step execution
│   │   ├── orchestrator.py        # Coordinates planner → workflow → reviewer
│   │   └── reviewer.py            # Mandatory structured review
│   ├── agents/                    # 16 specialized agents
│   │   ├── note_agent.py          # CRUD for notes
│   │   ├── vault_agent.py         # Vault inspection/validation
│   │   ├── search_agent.py        # Full-text/tag/property search
│   │   ├── folder_agent.py        # Folder create/move/analyze
│   │   ├── linking_agent.py       # Wikilinks, broken links, orphans, hubs
│   │   ├── metadata_agent.py      # Frontmatter/YAML property management
│   │   ├── template_agent.py      # Template discovery/apply
│   │   ├── periodic_agent.py      # Daily/weekly/monthly notes
│   │   ├── canvas_agent.py        # Obsidian Canvas (.canvas JSON)
│   │   ├── dashboard_agent.py     # MOC/index/dashboard generation
│   │   ├── bulk_agent.py          # Multi-file batch operations
│   │   └── graphify_agent.py      # Semantic graph intelligence
│   ├── integrations/
│   │   └── graphify/              # Graphify integration layer
│   │       ├── graphify_client.py         # CLI subprocess wrapper
│   │       ├── graphify_runner.py         # Build/query lifecycle + caching
│   │       ├── graphify_config.py         # Workspace paths
│   │       ├── graphify_models.py         # EdgeKind, GraphNode, GraphEdge, GraphAnalysis
│   │       ├── graphify_mcp.py            # MCP stdio client adapter
│   │       ├── graphify_brain.py          # Brain orchestrator
│   │       ├── graphify_brain_config.py   # Backend config (secrets-free)
│   │       └── graphify_brain_llm.py      # LLM client + OpenCode adapter + proxy
│   └── skills/
│       ├── __init__.py            # Skill registry + registered skills
│       └── ...
├── tests/                         # Test suite (67+ passing)
├── docs/                          # Documentation
├── scripts/                       # Utility scripts
├── graphify/                      # Graphify artifacts (graphs, validation vaults)
├── config/ohsc.json               # Runtime configuration
├── capabilities/                  # Machine-readable capability manifest
├── skills/                        # Agent-facing skill docs
├── snapshots/                     # Backup snapshots
├── logs/                          # Rotating logs + audit
├── memory/                        # System memory (JSON)
├── index/                         # Vault index cache
└── [report files]                 # Various validation/review reports
```

---

## 4. Core Infrastructure (`ohsc/core/`)

### 4.1 Configuration (`config.py`)

**`SystemConfig`** dataclass — single source of truth for ALL paths, safety, logging, backup, and testing config.

| Field | Default | Purpose |
|---|---|---|
| `system_root` | `D:\HOSC` | System workspace |
| `vault_root` | `D:\Mudassir database` | Obsidian vault |
| `allowed_roots` | `[system_root, vault_root]` | PathSafety allowed roots |
| `safety_mode` | `"strict"` | strict/normal |
| `dry_run_default` | `False` | Default dry-run behavior |
| `log_level` | `"INFO"` | Logging level |
| `log_dir` | `system_root/logs` | Log directory |
| `log_max_bytes` | 2,000,000 | Rotating log max size |
| `log_backups` | 5 | Rotating log backup count |
| `memory_dir` | `system_root/memory` | Memory store directory |
| `index_enabled` | `True` | Enable vault indexing |
| `index_dir` | `system_root/index` | Index cache directory |
| `backup_enabled` | `True` | Enable snapshots |
| `backup_dir` | `system_root/snapshots` | Snapshot storage |
| `test_vault_root` | `system_root/tests/fixtures/test_vault` | Isolated test vault |
| `require_explicit_destructive_auth` | `True` | Force auth for destructive ops |

**Override mechanism:**
- Environment variables: `OHSC_SYSTEM_ROOT`, `OHSC_VAULT_ROOT`
- JSON file: `D:\HOSC\config\ohsc.json`
- Loading: `load_config()` (singleton, lazy, fallback to defaults on error)

### 4.2 Contracts (`contracts.py`)

Structured communication protocol between agents:

**`OpClass`** (Enum):
- `READ` — safe, no auth needed
- `WRITE` — authorized by explicit user request
- `DESTRUCTIVE` — requires `--authorized` flag

**`TaskStatus`** (Enum): `PENDING`, `RUNNING`, `SUCCESS`, `FAILURE`, `SKIPPED`, `ROLLED_BACK`

**`Task`** dataclass: Unit of work with `id`, `agent`, `action`, `target`, `op_class`, `params`, `depends_on`, `authorized`, `created_at`. Serializable via `to_dict()`/`from_dict()`.

**`AgentResult`** dataclass: Agent output with `task_id`, `agent`, `status`, `summary`, `data`, `errors`, `warnings`, `started_at`, `finished_at`, `duration_ms`. `ok()` returns True for SUCCESS/SKIPPED.

### 4.3 Path Safety (`path_safety.py`)

**Every filesystem operation MUST pass through `PathSafety.validate()`.**

- Validates path is inside allowed roots (`D:\HOSC` and vault)
- Rejects `..` traversal explicitly
- `safe_join(base, *parts)` — joins parts under a validated base
- `is_allowed(path)` — boolean check without exception
- `from_config()` — factory from SystemConfig

### 4.4 Permissions (`permissions.py`)

**`PermissionAgent`** classifies every operation:
- Maps operation names → `OpClass` via `_OPERATION_MAP`
- Heuristic fallback for unknown operations (keyword matching)
- `decide(operation, user_authorized)` → `PermissionDecision`
- `require(operation, user_authorized)` → raises `PermissionError` if blocked
- READ operations: always authorized
- WRITE operations: authorized by explicit user request
- DESTRUCTIVE operations: only with `--authorized` flag

### 4.5 Filesystem (`filesystem.py`)

**`VaultBackend`** (ABC): Abstract interface for vault access (exists, read_text, write_text, list_dir, mkdir, remove, move, walk).

**`FilesystemBackend`**: Disk-backed implementation. ALL operations pass through `PathSafety`. Designed so a future `ObsidianRestBackend` could implement the same interface without changing any agent.

### 4.6 Logging (`logging.py`)

- Rotating file handler (`ohsc.log`, 2MB, 5 backups) + console handler
- `record_event()` — structured audit records (JSON lines to `audit.log`)
- Fields: timestamp, task_id, agent, operation, target, result, duration_ms, errors, warnings
- `read_audit(limit)` — read recent audit records
- Thread-safe with lock

### 4.7 Validation (`validation.py`)

- `validate_task(task)` — ensures agent, action, op_class are set; destructive tasks must be authorized
- `validate_note_name(name)` — non-empty, no path separators (`/`, `\`, `..`)
- `validate_is_markdown(path)` — enforces `.md` extension
- `non_empty(value, field_name)` — raises if None/empty

### 4.8 Snapshot Agent (`snapshot_agent.py`)

**`SnapshotAgent`**: Captures file state before high-risk operations.

- `capture(paths, label)` → `Snapshot` (copies files to `D:\HOSC\snapshots\snap_<timestamp>_<count>/`)
- `restore(snap)` — writes backup content back to original paths
- `list_snapshots()` — lists all snapshot directories
- Manifest stored as `manifest.json` in each snapshot dir

### 4.9 Transaction Agent (`transaction_agent.py`)

**`TransactionAgent`**: Implements `PREPARE → SNAPSHOT → EXECUTE → VALIDATE → COMMIT` pattern.

- Takes: `label`, `affected_paths`, `execute` callable, `validate` callable, `reversible` flag
- On failure: attempts `ROLLBACK` from snapshot
- Reports honestly when rollback is not possible
- Returns `TransactionReport` (success, rolled_back, snapshot_id, steps, error)

### 4.10 Indexing (`indexing.py` + `index_store.py`)

**`indexing.py`** — parsing utilities:
- `FRONTMATTER_RE` — YAML frontmatter extraction
- `WIKILINK_RE` — `[[wikilink]]` extraction
- `TAG_RE` — `#tag` extraction
- `parse_frontmatter(text)` → `(properties_dict, body_text)`
- `NoteRecord` dataclass: path, title, tags, properties, links, backlinks, mtime

**`VaultIndex`** — incremental cache with persistence:
- `refresh(vault_root, force)` — incremental re-scan (only changed files based on mtime)
- `save()`/`load()` — JSON persistence to `vault_index.json`
- `_build_backlinks()` — computes reverse link graph
- Queries: `get_note(title)`, `search_text(query)`, `search_tag(tag)`, `orphans()`, `hubs()`

### 4.11 Memory (`memory.py`)

**`MemoryStore`**: JSON-backed key-value storage per namespace.

- Namespaces: `system`, `agent`, `workflow`, `preferences`, `history`
- `set(namespace, key, value)` / `get(namespace, key)` / `append(namespace, key, item)`
- `history(limit)` — recent request history
- Files stored in `D:\HOSC\memory/<namespace>.json`

### 4.12 Agent Registry (`agent_registry.py`)

**`AgentContract`** dataclass: name, role, responsibilities, allowed_operations, input/output contracts, dependencies, permission_scope, reviewer_rules.

**`BaseAgent`** (ABC):
- Identity: `name`, `role`, `contract`
- `_wrap(task, fn)` — execution wrapper that times, catches exceptions, records audit events
- `execute(task)` — override in subclasses
- `health()` — override for health checks

**`AgentRegistry`**:
- `register(agent, enabled)` — stores agent + contract + enabled state
- `get(name)` → agent instance
- `dispatch(task)` → routes to correct agent, checks enabled state
- `list_agents()` → list of dicts with name, role, enabled, healthy, responsibilities
- `summary()` — formatted table output
- `count()` / `enabled_count()` — totals

### 4.13 Runtime (`runtime.py`)

**`Runtime`**: Bootstraps all shared infrastructure in one object.

```python
Runtime(config) →
  .safety     = PathSafety(allowed_roots)
  .backend    = FilesystemBackend(safety)
  .registry   = AgentRegistry()
  .memory     = MemoryStore(system_root)
  .index      = VaultIndex(backend, index_dir)
  .snapshot_agent = SnapshotAgent(backend, backup_dir)
  .transaction_agent = TransactionAgent(snapshot_agent)
  .workflow   = WorkflowEngine(registry)
```

### 4.14 Planner (`planner.py`)

**`PlannerAgent`**: Converts natural-language requests → `WorkflowPlan` (list of `Task` objects).

**Intent routing** (`INTENT_RULES`): 98 rules mapping keyword phrases → (agent, action, op_class). Graph-specific rules placed FIRST to avoid greedy matches. Examples:

| Keyword Phrase | Agent | Action | OpClass |
|---|---|---|---|
| `"shortest path"` | `graphify_agent` | `shortest_path` | READ |
| `"knowledge graph"` | `graphify_agent` | `build` | READ |
| `"create note"` | `note_agent` | `create` | WRITE |
| `"delete"` | `note_agent` | `delete` | DESTRUCTIVE |
| `"search"` | `search_agent` | `search_text` | READ |
| `"moc"` | `dashboard_agent` | `create_moc` | WRITE |
| `"daily"` | `periodic_agent` | `create_daily` | WRITE |

**Parameter extraction** (`_extract_params`): Regex-based extraction of structured params (title, content, query, tag, topic, source, target, node) from NL requests.

### 4.15 Workflow Engine (`workflow_engine.py`)

**`WorkflowEngine`**: Executes `WorkflowPlan` against the agent registry.

- Dependency-aware: `_resolve_ready(plan, done)` finds tasks whose dependencies are met
- Sequential execution with dependency ordering (no parallelism by default)
- Gates destructive tasks on authorization
- Stops on first failure (fail-fast)
- Returns `WorkflowReport` (name, passed, steps, timestamps)

### 4.16 Orchestrator (`orchestrator.py`)

**`Orchestrator`**: Coordinates the full request lifecycle.

```python
handle(request, authorized, dry_run, skip_review) →
  1. plan = planner.plan(request, authorized)
  2. if dry_run: convert WRITE/DESTRUCTIVE to no-op inspect
  3. report = workflow.run(plan)
  4. review = reviewer.review_workflow(report)
  5. if passed: memory.append("history", "requests", {...})
  6. return {request, plan_steps, report, review, status}
```

### 4.17 Reviewer (`reviewer.py`)

**`ReviewerAgent`**: Mandatory independent review.

**`review_workflow(report)`** — inspects:
1. Did every step complete?
2. Any errors emitted?
3. Unintended vault changes? (via dry-run diff + path safety)
4. Warnings

Returns `ReviewReport` (status: PASS/PASS_WITH_WARNINGS/FAIL, issues, recommendations, required_fixes, approved).

**`review_agent_module(path)`** — static review of agent code:
- Checks for class definition, execute() method, logging, path safety usage

---

## 5. Agents (`ohsc/agents/`) — All 16

### 5.1 Note Agent (`note_agent.py`)
- **Role:** `note_crud`
- **Operations:** create, read, update, append, rename, delete
- **Safety:** Read always safe; write needs authorization; delete is DESTRUCTIVE
- **Never silently deletes notes**

### 5.2 Vault Agent (`vault_agent.py`)
- **Role:** `vault_management`
- **Operations:** inspect, validate
- **Purpose:** Verify vault path exists, is an Obsidian vault, count markdown files

### 5.3 Search Agent (`search_agent.py`)
- **Role:** `search_query`
- **Operations:** search_text, search_tag, search_filename, search_property
- **Uses index for speed; fallback to direct filesystem walk**
- **Modes:** text, tag, filename, property

### 5.4 Folder Agent (`folder_agent.py`)
- **Role:** `folder_structure`
- **Operations:** create_folder, rename_folder, move_note, analyze
- **Analyzes folder organization**

### 5.5 Linking Agent (`linking_agent.py`)
- **Role:** `linking_graph`
- **Operations:** link (create wikilink), analyze (orphans, hubs, broken links)
- **Evidence-based linking** — never blindly adds links
- **`_broken_links()`** — detects links to non-existent notes

### 5.6 Metadata Agent (`metadata_agent.py`)
- **Role:** `properties_metadata`
- **Operations:** read_property, update_property, normalize
- **Preserves unrelated existing metadata**
- **Normalizes tags** (lowercase, sorted, list format)

### 5.7 Template Agent (`template_agent.py`)
- **Role:** `template`
- **Operations:** apply_template, list_templates, create_template
- **Templates stored in `_templates/` folder in vault**

### 5.8 Periodic Agent (`periodic_agent.py`)
- **Role:** `periodic_notes`
- **Operations:** create_daily, create_weekly, create_monthly
- **Avoids duplicate notes** — detects existing before creation

### 5.9 Canvas Agent (`canvas_agent.py`)
- **Role:** `canvas`
- **Operations:** create_canvas, read_canvas, add_node
- **Validates canvas JSON structure** (requires nodes + edges arrays)

### 5.10 Dashboard Agent (`dashboard_agent.py`)
- **Role:** `dashboard_moc`
- **Operations:** create_moc, create_index, create_dashboard
- **Collects related notes by topic keyword in title or tags**
- **Generates `[[wikilinks]]` to related notes**

### 5.11 Bulk Agent (`bulk_agent.py`)
- **Role:** `bulk_operations`
- **Operations:** bulk_append, bulk_tag, bulk_move, bulk_preview
- **Supports selector by tag or title contains**
- **Preview mode**, dry-run, transaction + rollback
- **Reports partial failures**

### 5.12 Graphify Agent (`graphify_agent.py`)
- **Role:** `graph_intelligence`
- **Operations:** build, query, shortest_path, explain, analyze
- **READ-ONLY on the vault** — writes only to `D:\HOSC\graphify`
- **Delegates to GraphifyRunner → GraphifyClient**
- **Requires authorization** (`--authorized`)
- **Verifies vault exists and is Obsidian** before execution
- **Health check:** reports Graphify availability
- **Complements** (does NOT replace) `linking_agent`

---

## 6. Graphify Integration (`ohsc/integrations/graphify/`)

### 6.1 Architecture

```
GraphifyAgent → GraphifyRunner → GraphifyClient → graphify CLI (subprocess)
                    ↓
              GraphifyBrain → GraphifyBrainLLM → OpenCode/OpenAI backend
                    ↓
              GraphifyBrainProxy (local /v1/chat/completions for Graphify)
```

### 6.2 GraphifyClient (`graphify_client.py`)

Thin, safe wrapper around the `graphify` CLI. All subprocess calls go through this class.

**Key features:**
- **Circuit breaker**: After 3 consecutive failures, short-circuits for 30s cooldown
- **Transient retry**: 2 retries with exponential backoff for timeout/network errors
- **Environment isolation**: Strips `PYTHONPATH` to prevent host venv shadowing Graphify's numpy/openai
- **Detection**: Checks PATH for `graphify`, falls back to `python -m graphify`

**Operations:**
- `build_graph(source_dir, out_dir)` — runs `graphify extract`, moves artifacts to OHSC workspace, cleans vault
- `query(question, graph_path, mode)` — runs `graphify query/path/explain`
- `shortest_path(source, target, graph_path)` — undirected by default
- `explain(node, graph_path)` — provenance + connections
- `version()` — installed graphify version

**Result types:**
- `GraphBuildResult`: ok, graph_path, html_path, report_path, version, error, stdout, stderr
- `GraphQueryResult`: ok, query, answer, error, raw

### 6.3 GraphifyRunner (`graphify_runner.py`)

Orchestrates build/query lifecycle with caching.

- **Caching:** Tracks graph version + vault mtime in `graph_meta.json`; reuses valid graph
- **`needs_rebuild()`** — checks graph exists, metadata valid, vault mtime newer
- **`build(force)`** — builds or reuses existing graph
- **`query/shortest_path/explain`** — delegates to client with existing graph

### 6.4 GraphifyBrain (`graphify_brain.py`)

The LLM intelligence layer backing Graphify.

- **`GraphifyBrainConfig`** — secrets-free config (provider, endpoint, model, key_env)
- **`GraphifyBrainLLM`** — OpenAI-compatible `chat()` client (urllib, stdlib only)
- **`OpenCodeBrainBackend`** — drives `opencode run -m <model> --format json --pure --auto`
  - Prompt piped via STDIN (Windows argv length limit)
  - Parses JSON stream events for model text
- **`GraphifyBrainProxy`** — local HTTP server exposing `/v1/chat/completions`
  - Graphify pointed at it via `OPENAI_BASE_URL`
  - Forwards to chosen backend (OpenCode/OpenAI/OpenRouter/Groq)

**Supported backends:**

| Provider | Key Env | Endpoint | Model |
|---|---|---|---|
| `opencode` | `OPENCODE_API_KEY` | `http://127.0.0.1:8848/v1` | `opencode/hy3-free` |
| `openai` | `OPENAI_API_KEY` | `https://api.openai.com/v1` | `gpt-4o-mini` |
| `openrouter` | `OPENROUTER_KEY_1` | `https://openrouter.ai/api/v1` | `openai/gpt-4o-mini` |
| `groq` | `GROQ_KEY_1` | `https://api.groq.com/openai/v1` | `llama-3.1-8b-instant` |

**Configuration env vars:**
- `GRAPHIFY_BRAIN_BACKEND` — provider selection
- `GRAPHIFY_BRAIN_ENDPOINT` — endpoint override
- `GRAPHIFY_BRAIN_MODEL` — model override
- `GRAPHIFY_BRAIN_KEY_ENV` — key env var name override
- `GRAPHIFY_BRAIN_TIMEOUT` — per-request timeout
- `GRAPHIFY_BRAIN_LOG_LEVEL` — log level

### 6.5 Graphify Models (`graphify_models.py`)

- `EdgeKind`: `EXTRACTED` (explicit, real wikilink) vs `INFERRED` (semantic, discovered by model)
- `GraphNode`: id, label, kind, community, metadata
- `GraphEdge`: source, target, kind, label, confidence
- `GraphAnalysis`: nodes, edges, communities, hubs, orphans

### 6.6 Graphify MCP (`graphify_mcp.py`)

MCP stdio client for Graphify's graph server.

**Relevant tools:** `query_graph`, `get_node`, `get_neighbors`, `god_nodes`, `graph_stats`, `shortest_path`, `get_community`

**PR tools excluded** (code-repo specific): `list_prs`, `get_pr_impact`, `triage_prs`

**`is_available()`** — real round-trip probe (initialize handshake), not just PATH check.

---

## 7. Universal Capability Gateway (`ohsc/gateway.py`)

Thin, agent-facing access layer for external coding/AI agents.

**Commands:**
- `ohsc activate` — activation + status check (returns ACTIVE/DEGRADED)
- `ohsc capabilities` — human-readable capability summary
- `ohsc capabilities --json` — full machine-readable manifest
- `ohsc status` — per-component health checks
- `ohsc agents` — list registered agents

**`capability_manifest()`** returns:
- `ohsc`: name, root, version, description
- `capability_groups`: graphify (operations, mcp_tools, safety), agents, orchestrator
- `supported_external_agents`: OpenCode, Claude Code, any CLI agent
- `interfaces`: cli, mcp, python
- `vault`: authorized_root, read_only
- `safety`: rules list

**`activation_status()`** checks:
1. Installation present
2. Python version
3. Configuration valid
4. Agent registry loaded
5. Graphify available
6. Graphify Brain config
7. OpenCode backend
8. Environment variables
9. MCP capability

**Security:** API keys are NEVER exposed — only env-var names and boolean presence flags.

---

## 8. Skills System (`ohsc/skills/`)

Reusable, documented, versionable procedures.

**`Skill`** dataclass: name, description, version, callable, tags

**Registered skills:**
- `frontmatter_rw` — read/write YAML frontmatter safely
- `wikilink_extract` — extract `[[wikilinks]]` from markdown
- `add_related_section` — add "## Related Notes" section without duplicating links

**Utility functions:**
- `_read_frontmatter(text)` / `_write_frontmatter(fm, body)`
- `_extract_wikilinks(text)` — regex extraction
- `_safe_add_related_section(body, links)` — idempotent link addition

---

## 9. CLI (`ohsc/cli.py`)

**Usage:**
```bash
python -m ohsc.cli "<request>" [--dry-run] [--authorized] [--no-review] [--json]
python -m ohsc.cli --agents
python -m ohsc.cli --graphify build|query|path|explain|analyze [--source X] [--target Y] [--node Z]
python -m ohsc.cli activate|capabilities|status|agents [--json]
```

**Flags:**
- `--dry-run` — preview only, no writes
- `--authorized` — explicit permission for destructive ops
- `--no-review` — skip reviewer (not recommended)
- `--json` — raw JSON output
- `--agents` — list registered agents

**Graphify direct mode:**
- `--graphify build` — build knowledge graph
- `--graphify query "..."` — semantic query
- `--graphify path --source A --target B` — shortest path
- `--graphify explain --node X` — explain concept
- `--graphify analyze` — structural report

---

## 10. Request Lifecycle (Detailed)

```
1. User: ohsc "Create a note titled Hello"
2. CLI → build_runtime() → Orchestrator
3. Orchestrator.handle("Create a note titled Hello")
4. Planner.plan() → WorkflowPlan with 1 Task:
   - agent: note_agent
   - action: create
   - op_class: WRITE
   - params: {title: "Hello", content: "", request: "..."}
5. WorkflowEngine.run(plan) → dispatches Task to NoteAgent.execute()
6. NoteAgent: PathSafety.validate(path) → backend.write_text(path, content)
7. Returns AgentResult(status=SUCCESS, summary="Created Hello.md")
8. ReviewerAgent.review_workflow(report) → PASS
9. Memory records successful pattern
10. Returns {status: "SUCCESS", report: ..., review: ...}
```

---

## 11. Safety Guarantees

1. **All file access validated** against allowed-root list via `PathSafety`
2. **Path traversal blocked** — `..` components rejected explicitly
3. **DESTRUCTIVE operations** require explicit `--authorized` flag
4. **Bulk operations** support `--dry-run` and snapshot-based rollback
5. **System files never live inside the vault**; vault data never lives inside the system folder
6. **Graphify is READ-ONLY** on the vault — writes only to `D:\HOSC\graphify`
7. **API keys never hardcoded** — referenced by env-var name only
8. **Every operation audited** — structured audit log with timestamp, task, agent, result, duration
9. **Transaction + rollback** — PREPARE→SNAPSHOT→EXECUTE→VALIDATE→COMMIT pattern
10. **Reviewer mandatory** — independent verification before declaring success

---

## 12. Test Suite

**Location:** `tests/`

**Test files:**
- `test_core.py` — path safety, permissions, validation, transactions
- `test_graphify_agent.py` — agent registration, vault safety, routing
- `test_graphify_brain.py` — Brain config, LLM client, proxy
- `test_graphify_mcp.py` — MCP adapter (skipped if unavailable)
- `test_graphify_runner.py` — runner lifecycle, caching
- `test_graphify_config.py` — workspace configuration
- `test_graphify_installation.py` — binary detection
- `test_graphify_routing.py` — intent routing
- `test_graphify_vault_safety.py` — vault read-only verification
- `test_integration.py` — end-to-end integration
- `test_e2e.py` — full E2E scenarios
- `test_gateway.py` — gateway activation, capabilities
- `test_external_agent_simulation.py` — external agent workflow
- `conftest.py` — shared fixtures (isolated temp vaults)

**Test vaults** (isolated, never touch real vault):
- `graphify/validation/basic/` — 29 nodes, 19 links
- `graphify/validation/intermediate/` — 19 nodes, 34 links
- `graphify/validation/advanced/` — 41 nodes, 89 links

**Running:**
```bash
cd D:\HOSC
python -m pytest tests/ -q
```

**Results:** 67+ passed, 3-6 skipped (MCP tests when server unavailable), 0 failed.

---

## 13. Measured Performance

| Metric | Value |
|---|---|
| `ohsc activate` e2e shell | 7.26s |
| `activation_status()` | 2711ms |
| Capability discovery | ~0ms (dict build) |
| Agent discovery | ~0ms |
| Cached graphify query | 7670ms |
| Basic vault build (29 nodes) | 57.6s |
| Intermediate vault build (19 nodes) | 76.4s |
| Advanced vault build (41 nodes) | 84.1s |

---

## 14. Known Limitations

1. **NL parsing** uses deterministic intent rules + regex (not an LLM). Complex compound requests may need splitting.
2. **Index is a cache** — safety-critical reads re-verify against disk.
3. **Obsidian REST API backend** — designed-for (abstraction exists) but not yet implemented; filesystem remains first-class.
4. **Rollback is mechanical** — file-level snapshot/restore; honest about when it cannot guarantee reversal.
5. **MCP server** — optional, may not launch on all platforms (missing `mcp` SDK / `pywintypes`); CLI is the primary interface.
6. **Graphify query semantics** — returns "No matching nodes found" for free-text meta-questions (node-label match); `path`/`explain`/`god_nodes` are more reliable.
7. **OpenCode backend** — requires billing method on OpenCode workspace; adapter is implemented and tested for shape.

---

## 15. How to Add a New Agent

1. Create `ohsc/agents/my_agent.py` subclassing `BaseAgent`
2. Define `contract = AgentContract(...)` and implement `execute()`
3. Add one `rt.registry.register(MyAgent(rt))` line in `ohsc/system.py`
4. Add unit/integration tests under `tests/`
5. The core architecture is unchanged; only the registry grows

---

## 16. External Agent Integration

**One-command activation:**
```bash
ohsc activate          # from ANY directory
ohsc capabilities --json
ohsc agents --json
```

**Workflow:**
1. Discover OHSC (shim on PATH or `D:\HOSC`)
2. Read `skills/OHSC_AGENT_SKILL.md` (agent-facing manual)
3. Read `capabilities/capabilities.json` (machine-readable manifest)
4. Activate: `ohsc activate` → expect `Status: ACTIVE`
5. Discover: `ohsc capabilities --json`, `ohsc agents --json`
6. Execute: `ohsc "build a knowledge graph"`, `ohsc --graphify build "<vault>"`
7. Verify structured result (status, success, error)

**Supported external agents:** OpenCode, Claude Code, Omni Router, OpenClaw, any CLI coding agent.

---

## 17. Deliverables Summary

| Category | Files |
|---|---|
| Core package | `ohsc/` (45+ Python files) |
| Tests | `tests/` (15 test files, 67+ tests) |
| Documentation | `docs/` (8+ markdown files) |
| Graphify validation | `graphify/validation/{basic,intermediate,advanced}/` |
| Reports | `GRAPHIFY_BRAIN_FINAL_REPORT.md`, `FINAL_TEST_REPORT.md`, etc. |
| Scripts | `scripts/` (20+ utility scripts) |
| Config | `config/ohsc.json` |
| Skills | `skills/OHSC_AGENT_SKILL.md` |
| Gateway | `capabilities/capabilities.json` |
| Snapshots | `snapshots/` (backup storage) |

---

**End of context_README.md** — This file captures the complete functional specification of the OHSC system as understood from reading every source file in the project.
