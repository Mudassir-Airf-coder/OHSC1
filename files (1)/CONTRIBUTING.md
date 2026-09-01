# Contributing to OHSC

Thanks for contributing. OHSC has a deliberate architecture (see
`README.md` → Architecture, and `docs/architecture/`) — please preserve
it rather than routing around it.

## Development setup

```bash
git clone <this-repo-url>
cd OHSC1
export OHSC_SYSTEM_ROOT=/tmp/ohsc-dev
export OHSC_VAULT_ROOT=/tmp/ohsc-dev-vault
pip install pytest --break-system-packages   # only third-party dep needed for dev
python -m pytest
```

Never point `OHSC_VAULT_ROOT` at a real Obsidian vault while developing
or testing — use a throwaway directory or the fixture vaults under
`tests/graphify_brain_validation/`.

## Project structure

See the tree in `README.md`. In short: core control-plane logic lives in
`ohsc/core/`, specialized behavior lives in `ohsc/agents/`, external
integrations (Graphify) live in `ohsc/integrations/`, and all
documentation lives in `docs/` plus the root-level `*.md` files.

## Adding an agent

1. Create `ohsc/agents/<name>_agent.py`, subclassing `BaseAgent`
   (`ohsc/core/agent_base.py`) and defining `name`, `role`, `contract`
   (an `AgentContract`), and `execute(task) -> AgentResult`.
2. Register it with one line in `ohsc/system.py`'s `build_runtime()`.
3. Add its routing rule(s) to `INTENT_RULES` in `ohsc/core/planner.py`
   if it should be reachable via natural language.
4. Add it to `ohsc/capabilities.json` **and** `capabilities/capabilities.json`
   (see `docs/GAPS.md` GAP-003 — keep both in sync until that
   duplication is resolved).
5. Document it in `docs/agents/` following the existing agent doc
   template (role, purpose, responsibilities, allowed operations,
   inputs/outputs, dependencies, permissions, safety rules, failure
   modes, examples).
6. Add tests under `tests/`.

Do not implement filesystem access directly in an agent — always go
through the injected `VaultBackend`/`PathSafety`, matching every
existing agent.

## Adding a skill

Runtime skills (reusable procedures, not documentation) live in
`ohsc/skills/__init__.py`. Register a `Skill(name, description, version,
callable, tags)` via the module's `_register()` helper, following the
existing `frontmatter_rw` / `wikilink_extract` / `add_related_section`
examples. This is distinct from `skills/OHSC_AGENT_SKILL.md`, which is
the human/AI-agent-facing operating manual — update that file only when
the *external interface* changes, not for internal skill additions.

## Adding an integration

Follow the pattern in `ohsc/integrations/graphify/`: a `*_client.py`
(talks to the external tool/binary), a `*_config.py` (typed config, no
hardcoded secrets), and a `*_runner.py` or agent wrapper that enforces
the same `PathSafety`/permission rules as everything else. Document it
under `docs/integrations/`.

## Adding tests

- Use `tmp_path` / fixture vaults, never a real vault.
- If your test needs a specific vault layout, prefer extending the
  existing synthetic vaults under `tests/graphify_brain_validation/`
  over inventing a new hardcoded path.
- Do not hardcode `D:\...`-style paths in new tests — that's exactly
  the pattern tracked as GAP-001; use `OHSC_SYSTEM_ROOT`/`tmp_path`
  instead.

## Documentation expectations

- Every new agent/integration needs a corresponding doc under `docs/`.
- Don't claim a capability exists unless you've read the code that
  implements it (or written it yourself). If something is planned but
  not implemented, mark it explicitly as **FUTURE** — see
  `docs/architecture/FUTURE_MASTER_MCP_GENERATOR.md` for the pattern.

## Coding conventions

- Stdlib-first: the core package has zero third-party runtime
  dependencies today — don't add one without a clear reason and a
  corresponding update to `docs/installation/INSTALLATION_READINESS.md`.
- Structured contracts, not free text: agents communicate via `Task` /
  `AgentResult`, never ad-hoc dicts or strings.
- Every filesystem operation must go through `PathSafety`.
- Every agent must log via the existing `_wrap()`/`record_event()`
  pattern — don't add silent failure paths.

## Security expectations

- Never commit `.env` files, API keys, or vault data. `.gitignore`
  already excludes the obvious patterns — extend it rather than working
  around it if you add a new kind of local artifact.
- Never point tests at a real vault.
- If you find committed secrets or personal data (e.g. real usernames,
  real note content), report it — don't quietly rewrite git history
  yourself.

## Pull request expectations

- Describe what changed and why.
- If you touched `ohsc/core/`, explain how you preserved the existing
  Orchestrator → Planner → Workflow Engine → Agent Registry → Reviewer
  flow, or justify the deviation explicitly.
- Run `python -m pytest` (with `OHSC_SYSTEM_ROOT`/`OHSC_VAULT_ROOT` set)
  and include the result in the PR description.
- Update `docs/PROJECT_STATUS.md` and/or `docs/GAPS.md` if your change
  resolves or introduces a tracked gap.
