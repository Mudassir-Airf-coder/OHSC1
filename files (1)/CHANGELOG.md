# Changelog

This project has no formal release history yet — the repository's git
log currently contains a single commit (`Push OHSC project as-is`) with
no version tags. The entries below reflect the **current documented
state**, not a series of past releases. Do not treat "Unreleased" as
implying prior tagged versions exist.

## [Unreleased] — Initial documented project state (2026-09-01)

### Added (this documentation/organization pass)

- `README.md` rewritten from a one-line placeholder into a full project
  overview, grounded in direct source inspection.
- `docs/PROJECT_STATUS.md` — subsystem-by-subsystem verification table.
- `docs/GAPS.md` — 8 tracked gaps with evidence, root cause, and impact.
- `docs/installation/INSTALLATION_READINESS.md` — component-by-component
  install readiness audit.
- `SECURITY.md`, `CONTRIBUTING.md`, `CHANGELOG.md` (this file).
- `docs/REPOSITORY_PREPARATION_REPORT.md` — full audit summary.

### Verified, not changed

- Core architecture (Orchestrator → Planner → Workflow Engine → Agent
  Registry → Specialized Agents → Reviewer → Memory) — confirmed against
  source, left untouched.
- 12 specialized agents + 4 infrastructure agents (permission, snapshot,
  transaction, reviewer) registered in `ohsc/system.py`.
- Path safety, permission classification, snapshot/transaction logic —
  all read and confirmed working as designed.
- Test suite executed: 61 passed, 10 failed, 11 skipped (all failures
  traced to one root cause — see GAPS.md GAP-001).

### Known issues carried forward (not fixed in this pass — see GAPS.md)

- Hardcoded Windows-only default paths (GAP-001).
- 42MB `bin/gh.exe` binary committed to git (GAP-002).
- Duplicate `capabilities.json` files (GAP-003).
- Personal machine path in `skills/OHSC_AGENT_SKILL.md` (GAP-004).
- `snapshots/` runtime data committed and not gitignored (GAP-005).
- No `pyproject.toml`/packaging metadata (installation readiness).
