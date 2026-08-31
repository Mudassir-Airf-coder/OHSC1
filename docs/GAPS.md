# OHSC Gaps

## G-001 — Python packaging metadata missing
- **Severity:** P1
- **Component:** installation/distribution
- **Current behavior:** Source package exists, but repository tree has no `pyproject.toml`, `setup.py`, or `requirements.txt`.
- **Expected:** A fresh clone should have a reproducible install contract.
- **Evidence:** repository tree audit.
- **Root cause:** packaging metadata is not currently checked in.
- **Impact:** fresh-machine installation cannot be reproduced from standard Python packaging metadata alone.
- **Recommended next step:** add minimal packaging metadata without changing runtime architecture.

## G-002 — Fresh-machine launcher installation is not fully reproducible
- **Severity:** P1
- **Component:** gateway/installation
- **Current behavior:** prior validation proved `ohsc activate` through a local launcher/shim on the validation machine.
- **Expected:** a clean machine can install the launcher with one documented command.
- **Evidence:** existing validation report versus absence of package metadata in repository tree.
- **Root cause:** local launcher and repository distribution are not yet the same reproducible installation mechanism.
- **Impact:** portability/distribution risk.
- **Recommended next step:** package the CLI entry point and document platform-specific installation.

## G-003 — Graphify MCP runtime dependency is optional/environment-blocked
- **Severity:** P2
- **Component:** MCP
- **Current behavior:** MCP implementation exists, but prior validation reported missing `mcp`/`pywintypes` extras in the environment.
- **Expected:** MCP works when its optional dependencies are installed, with CLI fallback otherwise.
- **Evidence:** prior validation report.
- **Root cause:** environment dependency availability.
- **Impact:** MCP cannot be assumed available on every installation.
- **Recommended next step:** document/install the optional dependency set and add environment-specific CI when support is defined.

## G-004 — Machine-local paths remain in checked-in capability/config documentation
- **Severity:** P2
- **Component:** configuration/distribution
- **Current behavior:** capability/configuration data contains local paths used by the development/validation environment.
- **Expected:** distributed configuration should separate defaults from machine-specific settings.
- **Evidence:** `capabilities/capabilities.json` and `config/ohsc.json` are checked-in.
- **Impact:** cloning the repository on another machine may require manual path changes.
- **Recommended next step:** introduce a documented portable configuration mechanism; do not silently change current runtime behavior.

## G-005 — Root contains large/local binary material
- **Severity:** P2
- **Component:** Git hygiene
- **Current behavior:** repository tree contains `bin/gh.exe` (~42 MB) and `gh.zip` (~15 MB).
- **Expected:** distribution should clearly classify whether these binaries are required source artifacts or development conveniences.
- **Evidence:** repository tree audit.
- **Impact:** repository size and licensing/distribution complexity.
- **Recommended next step:** verify provenance/necessity before removing or relocating; do not delete blindly.

## G-006 — Formal CI/packaging validation is not established
- **Severity:** P2
- **Component:** GitHub readiness
- **Current behavior:** no verified CI workflow was established by this audit.
- **Expected:** reproducible CI installs the project and runs tests/import checks.
- **Impact:** regressions may not be caught automatically.
- **Recommended next step:** add CI only after packaging metadata is defined and the workflow can succeed on a clean runner.

## G-007 — Reviewer static shape warning
- **Severity:** P3
- **Component:** reviewer
- **Current behavior:** previous validation reported a warning for gateway/CLI/launcher modules being judged by an agent-class-shaped static check.
- **Expected:** infrastructure modules should be reviewed according to their actual role.
- **Impact:** noisy reviewer output, but prior reviewer approval remained true.
- **Recommended next step:** refine the reviewer rule when its contract is next changed; do not alter gateway architecture just to satisfy a false-positive shape check.
