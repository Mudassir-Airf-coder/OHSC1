# OHSC — Gap Report

This document lists genuine gaps found while auditing the repository
(reconnaissance + source review + test run on 2026-09-01). A gap being
listed here is **not** authorization to redesign the affected system —
see `docs/REPOSITORY_PREPARATION_REPORT.md` for what was and was not
changed.

Severity legend: `P0` blocking, `P1` high, `P2` medium, `P3` low.

---

### GAP-001 — Hardcoded Windows-only roots throughout core config and tests

- **Severity:** P1
- **Component:** `ohsc/config.py`, `ohsc/core/path_safety.py`,
  `ohsc/core/snapshot_agent.py`, `ohsc/capabilities.json`,
  `capabilities/capabilities.json`, `skills/OHSC_AGENT_SKILL.md`,
  most of `tests/`
- **Current behavior:** `DEFAULT_SYSTEM_ROOT` and `DEFAULT_VAULT_ROOT` in
  `ohsc/config.py` default to `Path(r"D:\HOSC")` and
  `Path(r"D:\Mudassir database")`. `PathSafety`'s docstring and
  `SnapshotAgent`'s docstring repeat the same literal roots. Roughly a
  dozen tests construct `PathSafety([r"D:\HOSC", r"D:\Mudassir database"])`
  or compare against `Path(r"D:\HOSC")` directly.
- **Expected behavior:** For a project whose stated goal (Section 8 of
  the task brief) is a future one-command, cross-platform installer, the
  default roots should be environment/OS-derived rather than a single
  developer's literal Windows drive letters and folder name, and tests
  should not assume a Windows path parser.
- **Evidence:** Running the test suite on Linux
  (`OHSC_SYSTEM_ROOT`/`OHSC_VAULT_ROOT` overridden) still produces 10
  failures, all tracing to the same cause — `Path(r"D:\HOSC")` is parsed
  as a *relative* path with a literal backslash in its name on POSIX, so
  `.resolve()` yields nonsense like
  `/home/claude/OHSC1/D:\HOSC/graphify`. See
  `tests/test_core.py::test_path_safety_blocks_traversal`,
  `tests/test_graphify_config.py::test_workspace_paths_outside_vault`,
  `tests/test_graphify_vault_safety.py::test_runner_writes_graph_outside_vault`,
  and the `test_external_agent_simulation.py` failures.
- **Root cause:** Roots were authored for one specific Windows machine and
  never parameterized for the environment they run in, beyond the two
  `OHSC_SYSTEM_ROOT`/`OHSC_VAULT_ROOT` env-var overrides that `config.py`
  already supports (which is the right mechanism — it's just not the
  default and the tests bypass it).
- **Impact:** Anyone (or any CI runner, or any AI coding agent per
  Section 15/16 of the task) that clones this repo on macOS/Linux, or a
  different Windows machine, gets a broken default install and a failing
  test suite out of the box. This directly blocks the "installation
  readiness" goal.
- **Recommended next step:** Not made in this pass (would touch
  `config.py` defaults and ~10 tests — an architectural/behavioral
  change, not a docs/organization change). Recommend deriving defaults
  from `platformdirs`-style OS conventions or an explicit first-run
  `ohsc init` step, and rewriting the affected tests to use
  `tmp_path`/env overrides instead of literal `D:\...` strings.

---

### GAP-002 — 42MB `bin/gh.exe` binary committed to git history

- **Severity:** P1
- **Component:** `bin/gh.exe` (git hygiene)
- **Current behavior:** A 42,166,072-byte Windows executable (the GitHub
  CLI, `gh.exe`) is tracked in git. It is by far the largest object in
  the repository's history.
- **Expected behavior:** Third-party tool binaries should not be
  committed to a source repository; they should be downloaded by an
  install/setup script or documented as a prerequisite.
- **Evidence:** `git rev-list --objects --all | git cat-file
  --batch-check` shows `blob ... 42166072 bin/gh.exe` as the largest
  blob by a wide margin (next largest tracked file is 31KB).
- **Root cause:** Unclear — likely committed for convenience during
  development on the original machine.
- **Impact:** Bloats clone size for every contributor, is
  platform-specific (Windows-only binary in a project that wants to be
  installable elsewhere), and its presence was explicitly called out for
  inspection in the task brief (which mentioned a similar `gh.zip`).
- **Recommended next step:** Remove `bin/gh.exe` from the working tree
  and `.gitignore` `bin/*.exe` going forward. Removing it from *history*
  (to reclaim clone size) requires a history rewrite, which this task's
  rules explicitly say to stop and report rather than do unilaterally —
  flagged here, not executed.

---

### GAP-003 — Duplicate, byte-identical `capabilities.json`

- **Severity:** P2
- **Component:** `capabilities/capabilities.json`, `ohsc/capabilities.json`
- **Current behavior:** Two capability manifests exist at different
  paths and are byte-for-byte identical.
- **Expected behavior:** One canonical machine-readable manifest, with
  the other path either removed or turned into a generated/symlinked
  copy.
- **Evidence:** `diff capabilities/capabilities.json
  ohsc/capabilities.json` → no output (identical).
- **Root cause:** Unclear — could be intentional (one for package
  introspection, one for repo-root tooling) or accidental duplication.
- **Impact:** Low immediate risk (they agree today), but a real risk of
  silent drift — a future edit to one and not the other would leave the
  gateway (`ohsc/gateway.py`, which is what actually gets imported at
  runtime) and any root-level tooling reading different capability
  sets.
- **Recommended next step:** Confirm with the maintainer which path is
  canonical, then have the other generated from it (or removed) rather
  than hand-maintained twice.

---

### GAP-004 — Personal machine path embedded in agent-facing docs

- **Severity:** P2
- **Component:** `skills/OHSC_AGENT_SKILL.md`
- **Current behavior:** The document states the vault "is located at
  `C:\Users\HAJI LAPTOP G55\Documents\Obsidian Vault`" and the
  activation example output claims `Key: CONFIGURED (OPENCODE_API_KEY)`.
- **Expected behavior:** Agent-facing reference docs meant to be read by
  any external AI coding agent (per Section 19) shouldn't bake in one
  person's real machine username/path as if it were a system constant.
- **Evidence:** Direct read of `skills/OHSC_AGENT_SKILL.md`, lines near
  the top of the "Purpose" section.
- **Root cause:** Doc was written against one developer's actual local
  setup rather than a generic example.
- **Impact:** Not a secret leak (no key value present), but it is
  personally identifying (a Windows username) and it will actively
  mislead any other user or agent that reads this file expecting it to
  describe their own environment.
- **Recommended next step:** Replace the literal path with a placeholder
  (e.g. `<your-vault-path>`) and note that the real path comes from
  `OHSC_VAULT_ROOT` / `config/ohsc.json`.

---

### GAP-005 — `snapshots/` (runtime backup data) is tracked in git and not gitignored

- **Severity:** P2
- **Component:** `.gitignore`, `snapshots/`
- **Current behavior:** 32 snapshot directories containing captured note
  content (including what looks like real vault note titles, e.g. "Graph
  Engineering by Adnan.md") are committed to the repository. `.gitignore`
  does not exclude `snapshots/`.
- **Expected behavior:** Per the system's own design
  (`ohsc/core/snapshot_agent.py`: "Snapshots are stored under
  `D:\HOSC\snapshots` and never inside the vault"), this is generated
  runtime/backup data, not source.
- **Evidence:** `find` listing of `snapshots/*/manifest.json` +
  `.gitignore` contents (only excludes `.env`, `*.log`, `__pycache__/`,
  `*.pyc`, `graphify/graphs/`, `graphify/validation/`, `validation/`,
  `auth.json`, `*.key`, `*credentials*` — no `snapshots/` entry).
- **Root cause:** Likely committed during development/testing and never
  added to `.gitignore`.
- **Impact:** Repo bloat, and possible unintended disclosure of personal
  note content/titles from whoever's vault produced these snapshots
  (nothing that reads like a credential was found, but the content is
  personal notes, not test fixtures).
- **Recommended next step:** Add `snapshots/` to `.gitignore` and confirm
  with the maintainer whether the already-committed snapshot content
  should be removed from the working tree (and, separately, from
  history — same history-rewrite caveat as GAP-002).

---

### GAP-006 — Root `README.md` is a one-line placeholder

- **Severity:** P1
- **Component:** `README.md`
- **Current behavior:** Contains exactly `# OHSC1` (7 bytes). All the
  real project narrative lives in `context_README.md` (31KB, root) and
  `SYSTEM_OVERVIEW.md` instead of the file GitHub actually renders on
  the repo's landing page.
- **Expected behavior:** `README.md` is the canonical entry point.
- **Evidence:** `cat README.md` output; `wc -c` = 7 bytes.
- **Root cause:** Appears the real overview was written into
  `context_README.md` as a working/context document and never promoted
  to `README.md`.
- **Impact:** Anyone landing on the GitHub repo page today sees nothing
  useful.
- **Recommended next step:** Addressed in this pass — see
  `README.md` (rewritten using verified information from
  `context_README.md`, `SYSTEM_OVERVIEW.md`, `docs/`, and direct source
  inspection; nothing invented).

---

### GAP-007 — MCP / Graphify runtime dependencies are absent in this environment

- **Severity:** P3 (environment-dependent, not necessarily a code bug)
- **Component:** Graphify integration, MCP
- **Current behavior:** `graphify-mcp` executable is not on `PATH`, and
  the `graphify` CLI probe (`python -m graphify`) fails, in the
  environment this audit ran in.
- **Expected behavior:** Documented as an optional external dependency —
  the system is expected to degrade gracefully when absent (per
  `ohsc/gateway.py`'s `DEGRADED` status, which is exactly what was
  observed).
- **Evidence:** `tests/test_graphify_installation.py::test_graphify_version_reported`
  and `::test_graphify_mcp_executable_present` fail with "graphify-mcp
  executable missing" / empty version string;
  `tests/test_gateway.py::test_activation_status_keys_present` shows the
  gateway correctly reporting `DEGRADED` rather than crashing.
- **Root cause:** `graphify` (the `graphifyy` PyPI package) and its MCP
  server are external, optional dependencies not installed in this
  sandboxed audit environment.
- **Impact:** None on system correctness — this is exactly the kind of
  environment issue the task brief asks to classify separately from real
  bugs — but it does confirm MCP is optional-dependency-gated, not
  built-in, which matters for `docs/integrations/MCP.md`.
- **Recommended next step:** No code change. Documented as MISSING
  OPTIONAL DEPENDENCY in the test classification (see `docs/PROJECT_STATUS.md`).

---

### GAP-008 — Two capability groups overlap in the Planner's keyword table

- **Severity:** P3
- **Component:** `ohsc/core/planner.py` (`INTENT_RULES`)
- **Current behavior:** Several tuples in `INTENT_RULES` are listed
  twice verbatim (e.g. `("shortest path", "graphify_agent",
  "shortest_path", OpClass.READ)` appears twice; the entire "Graph
  intelligence (Graphify)" block of ~13 rules is duplicated further down
  the list).
- **Expected behavior:** Since the loop does `if keyword in request_l and
  agent not in used`, duplicate entries are dead code — the first match
  always wins and the `used` guard means the duplicate can never fire.
- **Evidence:** Direct read of `ohsc/core/planner.py`.
- **Root cause:** Looks like a copy/paste artifact when the "most
  specific graph phrasings first" reordering was done — the older block
  was never deleted.
- **Impact:** No functional impact (dead code only), but it makes the
  routing table harder to audit and slightly larger than necessary.
- **Recommended next step:** Not changed in this pass per Rule 2 (safe
  but non-essential cleanup of working logic) — flagged for a future
  small, low-risk cleanup commit.
