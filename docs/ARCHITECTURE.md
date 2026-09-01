# OHSC Architecture

## Purpose

OHSC (Obsidian System Control) is a **local control plane** for Obsidian vaults. It converts natural-language or structured requests into authorized, auditable operations against Markdown vault files, and exposes the same surface to external AI agents through a CLI + skill contract.

## High-level flow

```text
Request
  → Planner (intent → WorkflowPlan of Tasks)
  → Workflow Engine (ordered execution + auth gates)
  → Agent Registry (dispatch to one of 16 agents)
  → PathSafety + Permissions
  → Filesystem backend and/or Graphify
  → Reviewer
  → Memory
```

## Core modules (`ohsc/core/`)

| Module | Responsibility |
|---|---|
| `contracts.py` | `Task`, `AgentResult`, op classes, statuses |
| `path_safety.py` | Allowed-root containment; blocks traversal |
| `permissions.py` | READ / WRITE / DESTRUCTIVE classification |
| `filesystem.py` | Vault backend abstraction |
| `planner.py` | NL → plan via intent rules |
| `workflow_engine.py` | Dependency-ordered execution |
| `orchestrator.py` | Plan → execute → review pipeline |
| `agent_registry.py` | Register / enable / dispatch agents |
| `reviewer.py` | Structured PASS / FAIL reports |
| `memory.py` | Namespaced memory / history |
| `indexing.py` | Vault index (notes, tags, links) |
| `snapshot_agent.py` | Snapshots before risky ops |
| `transaction_agent.py` | Prepare → snapshot → execute → validate |
| `session.py` | Session token for `ohsc run` |

## Agents (`ohsc/agents/`)

Sixteen specialized agents (see root README table). New agents are registered in `ohsc/system.py` without changing the orchestrator core.

## Graphify subsystem

Located under `ohsc/integrations/graphify/`.

Responsibilities:

- build / query / path / explain / analyze
- optional Graphify Brain LLM backend (OpenCode)
- optional MCP adapter for graph tools

OHSC remains the control plane; Graphify remains the graph engine.

## Gateway & CLI

- `ohsc/cli.py` — user and agent-facing commands
- `ohsc/gateway.py` — activation, capability manifest, status
- `skills/OHSC_AGENT_SKILL.md` — operating manual for external agents
- `capabilities/capabilities.json` — machine-readable capability list

## Safety invariants

1. No path outside allowed roots
2. No destructive op without explicit authorization
3. No secrets in repo or logs
4. Graphify analysis does not write into the user vault by default
5. Reviewer is part of the normal pipeline

## Configuration

Portable resolution order:

1. `OHSC_SYSTEM_ROOT` / `OHSC_VAULT_ROOT` environment variables
2. Package / repo location detection
3. Non-root settings from `config/ohsc.json`

## Non-goals (current)

- Controlling the Obsidian desktop application UI
- Claiming cloud one-click install before it exists
- Replacing Graphify with a different graph product under the same name
