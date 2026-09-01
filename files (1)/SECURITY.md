# Security

This document describes OHSC's safety architecture as implemented in
this repository, not as aspirational design. Every claim below is
grounded in a specific source file that was read during this audit.

## Path traversal protection

All filesystem access goes through `ohsc/core/path_safety.py`'s
`PathSafety` class:

- `.validate(path)` resolves the path, explicitly rejects any path
  containing a `..` traversal component, and then checks the resolved
  path is contained within one of the configured `allowed_roots`.
- `FilesystemBackend` (`ohsc/core/filesystem.py`) routes every read,
  write, list, mkdir, remove, move, and walk operation through
  `PathSafety.validate()` first — there is no bypass path in that class.

## Allowed roots

Roots are configured centrally in `ohsc/config.py`'s `SystemConfig`
(`system_root`, `vault_root`, and the derived `allowed_roots` list),
overridable via `OHSC_SYSTEM_ROOT` / `OHSC_VAULT_ROOT` environment
variables or `config/ohsc.json`. **Note:** the compiled-in defaults are
currently Windows-specific paths — see `docs/GAPS.md` GAP-001. Always
override them explicitly for any environment other than the original
development machine.

## Permissions (READ / WRITE / DESTRUCTIVE)

Every operation is classified by `ohsc/core/permissions.py`'s
`PermissionAgent`:

- **READ** operations are implicitly authorized.
- **WRITE** operations are authorized by the fact of an explicit user
  request.
- **DESTRUCTIVE** operations (`delete`, `mass_delete`, `mass_replace`,
  `purge`) require `authorized=True` to be explicitly passed; otherwise
  `PermissionAgent.require()` raises `PermissionError`, and
  `WorkflowEngine.run()` independently re-checks this at execution time
  before dispatching a destructive task.

## Destructive-operation authorization

Authorization is not automatic and is not inferred from context — it is
an explicit boolean the caller (CLI flag `--authorized`, or the
external-agent gateway) must set. The CLI prints a warning rather than
silently proceeding when it isn't set for Graphify's own operations.

## API key / secrets handling

- A full repository scan for literal API-key/token/password-shaped
  values (`grep` for key=value and key:"value" patterns of 15+
  characters) found **no committed secrets** as of this audit.
- `.gitignore` already excludes `.env`, `.env.*`, `auth.json`, `*.key`,
  and `*credentials*`.
- LLM backend keys (e.g. for Graphify Brain's OpenCode backend) are
  referenced by environment-variable name (`OPENCODE_API_KEY`) in
  `ohsc/integrations/graphify/graphify_brain_config.py` /
  `graphify_brain_llm.py`, never as literal values.
- If you ever find a tracked file that *does* contain a real secret,
  stop and report it rather than rewriting git history yourself —
  history rewrites need explicit, deliberate handling.

## Snapshots

Before high-risk operations, `ohsc/core/snapshot_agent.py`'s
`SnapshotAgent` copies affected files into a snapshot directory (default
under the system root's `snapshots/`, never inside the vault) with a
JSON manifest, so they can be restored via `.restore()`.

## Transactions

`ohsc/core/transaction_agent.py`'s `TransactionAgent` implements the
PREPARE → SNAPSHOT → EXECUTE → VALIDATE → COMMIT pattern and attempts a
ROLLBACK on failure where a snapshot exists. It is explicitly designed
to report honestly rather than claim a rollback succeeded when the
underlying operation isn't mechanically reversible.

## Audit logs

`ohsc/core/logging.py` provides rotating application logs plus
structured audit events (`record_event`) recorded by every agent
execution (`BaseAgent._wrap` in `agent_registry.py`) and by the workflow
engine.

## External integrations

The external-agent gateway (`ohsc/gateway.py`) exposes capabilities via
a structured manifest rather than arbitrary code execution — an
external agent discovers and calls named operations, it does not get
shell/filesystem access directly.

## Safe testing

The test suite uses isolated, synthetic fixture vaults
(`tests/graphify_brain_validation/{basic,intermediate,advanced}_vault`,
`tests/fixtures/`) rather than a real Obsidian vault. When
testing/validating this repository yourself, always point
`OHSC_VAULT_ROOT` at a throwaway directory — **never** at a real vault
you care about, and never run destructive operations against real user
data during automated testing.

## Known limitations (see `docs/GAPS.md` for full detail)

- Default paths are Windows-specific (GAP-001) — override before use
  elsewhere.
- A 42MB `bin/gh.exe` binary is committed to git (GAP-002) — not a
  secret, but unnecessary and should be removed.
- `snapshots/` contains committed runtime backup data with real note
  titles and is not currently gitignored (GAP-005).

## Vulnerability reporting

If you discover a security issue in this repository, open a GitHub
issue describing the problem without including any live secret values,
or contact the repository maintainer directly.
