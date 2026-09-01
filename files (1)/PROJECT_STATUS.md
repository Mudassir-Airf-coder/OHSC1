# OHSC — Project Status

Snapshot as of 2026-09-01, based on direct source inspection and a live
test run (`python3 -m pytest`, Python 3.12.3, Linux sandbox, with
`OHSC_SYSTEM_ROOT`/`OHSC_VAULT_ROOT` overridden to writable temp paths).

Status values: **VERIFIED** (evidence-backed), **PARTIALLY VERIFIED**,
**NOT VERIFIED** (plausible but unconfirmed in this environment),
**KNOWN GAP** (confirmed broken/missing — see `docs/GAPS.md`).

| Subsystem | Status | Basis |
|---|---|---|
| Contracts (`Task`/`AgentResult`/`OpClass`/`TaskStatus`) | VERIFIED | Read `ohsc/core/contracts.py`; used consistently across orchestrator/planner/registry/reviewer. |
| Permissions (READ/WRITE/DESTRUCTIVE) | VERIFIED | `ohsc/core/permissions.py` implements the classification map + heuristic fallback + `require()` gate; `workflow_engine.py` actually raises `PermissionError` on unauthorized destructive tasks. |
| Path Safety | VERIFIED (logic) / KNOWN GAP (defaults) | Traversal rejection and root-containment logic in `ohsc/core/path_safety.py` is sound and covered by tests; the *default* allowed roots are Windows-only literals — see GAP-001. |
| Filesystem Backend | VERIFIED | `ohsc/core/filesystem.py`: abstract `VaultBackend` + concrete `FilesystemBackend`, all operations routed through `PathSafety.validate()`. |
| Planner | VERIFIED | `ohsc/core/planner.py`: keyword→(agent, action, op_class) routing table + regex-based parameter extraction; has minor dead-code duplication (GAP-008), not a correctness issue. |
| Workflow Engine | VERIFIED | `ohsc/core/workflow_engine.py`: dependency-ordered execution, halts on first failing non-optional step, enforces authorization on DESTRUCTIVE tasks, records events. |
| Orchestrator | VERIFIED | `ohsc/core/orchestrator.py`: Plan → Execute → Review → Memory pipeline exactly as described in the architecture brief. |
| Agent Registry | VERIFIED | `ohsc/core/agent_registry.py`: registration, dispatch, enable/disable, introspection (`list_agents`, `summary`, `count`). |
| Reviewer | VERIFIED | `ohsc/core/reviewer.py`: structured `ReviewReport` with PASS/PASS_WITH_WARNINGS/FAIL, both workflow-level and static per-module review. |
| Memory | VERIFIED | `ohsc/core/memory.py`: namespaced JSON key/value + append/history, no destructive trust ("verified against the vault when needed" per its own docstring). |
| Indexing | VERIFIED | `ohsc/core/indexing.py` + `index_store.py`: incremental mtime-based rescans, frontmatter/wikilink/tag parsing, backlink graph, orphan/hub queries. |
| Snapshot / Backup | VERIFIED (logic) / KNOWN GAP (default path) | `ohsc/core/snapshot_agent.py` capture/restore logic works; default backup dir is under the same hardcoded `D:\HOSC` root (GAP-001). |
| Transactions (Prepare→Snapshot→Execute→Validate→Commit) | PARTIALLY VERIFIED | `ohsc/core/transaction_agent.py` exists and wires to `SnapshotAgent`; not fully read/exercised in this pass — recommend a follow-up read before documenting it in the architecture doc as fully verified. |
| Agents (12 specialized: vault, note, search, folder, linking, metadata, template, periodic, canvas, dashboard, bulk, graphify) | VERIFIED (registered) / NOT VERIFIED (individual internals) | All 12 are registered in `ohsc/system.py::build_runtime`. This pass confirmed registration and the base contract shape (`agent_base.py`); it did not deep-read every individual agent file — flagged for the docs/agents/ pass. |
| Skills system (`ohsc/skills/`) | VERIFIED | Code-level skill registry (`frontmatter_rw`, `wikilink_extract`, `add_related_section`) with name/description/version/tags, distinct from `skills/OHSC_AGENT_SKILL.md` (see below). |
| `skills/` vs `ohsc/skills/` distinction | VERIFIED | They serve different purposes and do NOT overlap confusingly: `ohsc/skills/` is the runtime skill-registration code used by agents; `skills/OHSC_AGENT_SKILL.md` is a human/AI-agent-facing operating manual. No merge needed. |
| Capability manifest (`capabilities.json`) | PARTIALLY VERIFIED | Exists in two identical copies (GAP-003); content structure (architecture list, capability groups, operations) matches the agents/integrations actually present. |
| Graphify integration | VERIFIED (code present) / NOT VERIFIED (live behavior) | Full client/runner/MCP/brain-config/brain-LLM stack exists under `ohsc/integrations/graphify/`. Live calls to the external `graphify` binary and `graphify-mcp` were not exercised — the binary isn't installed in this sandbox (GAP-007), and the gateway correctly reports `DEGRADED` rather than failing silently when it's absent. |
| MCP | PARTIALLY VERIFIED | `graphify_mcp.py` exists as an adapter; no standalone OHSC-level MCP server was found outside the Graphify integration. See `docs/integrations/MCP.md` for the detailed, code-grounded breakdown. |
| External AI-agent integration (Gateway) | VERIFIED | `ohsc/gateway.py` (307 lines) + `ohsc/capabilities.json` implement discovery/activation; `tests/test_external_agent_simulation.py` exercises this from three simulated external-agent perspectives (currently failing only due to GAP-001's path issue, not a logic error). |
| CLI | VERIFIED (present) / NOT VERIFIED (full command surface) | `ohsc/cli.py` (223 lines) and `ohsc_launcher.py` exist; this pass did not exhaustively exercise every CLI subcommand against a live vault. |
| One-command installer / packaging | KNOWN GAP | No `pyproject.toml`, `setup.py`, or `setup.cfg` found anywhere in the repo. There is currently no way to `pip install` OHSC or get a console-script entry point; `ohsc_launcher.py` is the closest thing to an entry point today. See `docs/installation/INSTALLATION_READINESS.md`. |
| Obsidian desktop app integration | NOT VERIFIED / LIKELY NOT IMPLEMENTED | Nothing in the source touches the Obsidian application (no plugin API calls, no REST/local-API client). All integration found is filesystem-level (`FilesystemBackend` reading/writing `.md` files directly). Documented as vault-filesystem integration only — do not claim desktop-app control. |
| Git hygiene | KNOWN GAP | `bin/gh.exe` (42MB) tracked in git; `snapshots/` (32 dirs of real note content) tracked and not gitignored. See GAP-002, GAP-005. |
| Secrets | VERIFIED CLEAN | Repository-wide scan for literal key/token/password-shaped values found none; `.gitignore` already excludes `.env`, `*.key`, `*credentials*`, `auth.json`. |
| Test suite | VERIFIED (ran it) | 61 passed, 10 failed, 11 skipped, 76 warnings in <1s. All 10 failures trace to the single Windows-path root cause in GAP-001 — classified as ENVIRONMENT ISSUE, not independent bugs. Full run log in `docs/REPOSITORY_PREPARATION_REPORT.md`. |

## Summary counts

- **VERIFIED:** 15 subsystems
- **PARTIALLY VERIFIED:** 4 subsystems
- **NOT VERIFIED (unconfirmed, not contradicted):** 3 subsystems
- **KNOWN GAP:** 5 items (cross-referenced in `docs/GAPS.md`)
