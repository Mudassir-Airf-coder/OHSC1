# OHSC — System Overview

## 1. Design Principles

OHSC follows the "control plane for Obsidian" principle. Key rules from
the build mandate that are enforced in code:

| Principle | Enforcement |
|-----------|-------------|
| No giant agent | 16 specialized agents, each with one responsibility |
| No hardcoded paths | Single `ohsc/config.py` `SystemConfig` source of truth |
| No silent failures | Every agent wrapped in `_wrap` → structured `AgentResult` |
| No unauthorized vault edits | `PathSafety` guard + `PermissionAgent` classification |
| No duplicate fs logic | `VaultBackend` abstraction (`FilesystemBackend`) |
| Observable | `core/logging.py` rotating + audit log |
| Recoverable | `TransactionAgent` snapshot/rollback |
| Extensible | New agent = definition + impl + register (one line) |

## 2. Request Lifecycle

```
1. Orchestrator.handle(request)
2. Planner.plan(request)  → WorkflowPlan (Tasks with params, op_class)
3. WorkflowEngine.run(plan) → dispatches each Task to its agent
4. Each agent: PathSafety.validate → execute → AgentResult (+ audit log)
5. ReviewerAgent.review_workflow(report) → PASS/FAIL + fixes
6. Memory records successful patterns
7. User-friendly final result returned
```

## 3. Core Modules (`ohsc/core/`)

| Module | Responsibility |
|--------|---------------|
| `config.py` | Single source of truth for paths, safety, logging, backup |
| `contracts.py` | `Task` / `AgentResult` / `OpClass` structured protocol |
| `path_safety.py` | Centralized allowed-root validation (mandatory) |
| `permissions.py` | READ / WRITE / DESTRUCTIVE classification + auth |
| `filesystem.py` | `VaultBackend` ABC + `FilesystemBackend` (safe disk I/O) |
| `logging.py` | Rotating logs + structured audit trail |
| `validation.py` | Input/contract validation |
| `snapshot_agent.py` | Capture/restore affected files |
| `transaction_agent.py` | PREPARE→SNAPSHOT→EXECUTE→VALIDATE→COMMIT + rollback |
| `indexing.py` / `index_store.py` | Incremental vault index (notes, tags, links, backlinks) |
| `memory.py` | System/agent/workflow/preference/history memory |
| `agent_registry.py` | `BaseAgent`, `AgentContract`, `AgentRegistry` |
| `agent_base.py` | Canonical base import |
| `runtime.py` | Bootstraps all shared infrastructure |
| `planner.py` | NL → structured plan + parameter extraction |
| `workflow_engine.py` | Sequential/parallel step execution |
| `orchestrator.py` | Coordinates planner → workflow → reviewer |
| `reviewer.py` | Mandatory structured review |

## 4. Agents (`ohsc/agents/`)

16 agents — see `AGENTS_INDEX.md`. The newest is `graphify_agent`, a
semantic graph-intelligence layer (READ-ONLY on the vault) that delegates to
the Graphify CLI/MCP and writes graph artifacts only to `D:\HOSC\graphify`. It
complements `linking_agent` (structural wikilinks) and `dashboard_agent`
(MOCs); the Reviewer approves the final result.

## 5. Skills (`ohsc/skills/`)

Reusable, documented, versionable procedures (frontmatter read/write,
wikilink extraction, tag extraction). Discoverable via `SkillRegistry`.

## 6. Configuration

`SystemConfig` in `ohsc/config.py` is the single source of truth.
Override via environment variables `OHSC_SYSTEM_ROOT` / `OHSC_VAULT_ROOT`,
or the JSON file `D:\HOSC\config\ohsc.json`.

## 7. Known Limitations

- Natural-language parsing uses deterministic intent rules + regex
  parameter extraction (not an LLM). Complex compound requests may need
  to be split by the user.
- The index is a cache; safety-critical reads re-verify against disk.
- The Obsidian Local REST API backend is designed-for (abstraction exists)
  but not yet implemented; filesystem remains first-class.
- Rollback is mechanical (file-level snapshot/restore); it is honest about
  when it cannot guarantee reversal.
