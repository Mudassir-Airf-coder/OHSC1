# OHSC — Installation Readiness Audit

Audits the repository against the future "one command → install →
configure → detect Obsidian → configure vault → configure Graphify →
activate → READY" vision. This document does **not** implement that
installer; it inventories what already supports it.

Status values: **READY**, **PARTIALLY READY**, **NOT READY**.

| Component | Status | Notes |
|---|---|---|
| Python packaging (`pip install`-able) | **NOT READY** | No `pyproject.toml`, `setup.py`, or `setup.cfg` anywhere in the repo. `ohsc` cannot currently be installed as a package or invoked from outside the repository directory without manual `PYTHONPATH`/cwd setup. |
| CLI entry point | **PARTIALLY READY** | `ohsc/cli.py` and `ohsc_launcher.py` exist and implement command dispatch, but there is no console-script entry point (`ohsc = ohsc.cli:main`-style) registered anywhere, since there's no packaging metadata to register it in. |
| Cross-platform default paths | **NOT READY** | `ohsc/config.py` hardcodes `D:\HOSC` and `D:\Mudassir database` as defaults. Overridable via `OHSC_SYSTEM_ROOT`/`OHSC_VAULT_ROOT` env vars (that mechanism is READY), but the *defaults* only make sense on one specific Windows machine. See GAPS.md GAP-001. |
| Dependency footprint | **READY** | Core `ohsc/` package (contracts, orchestrator, planner, workflow engine, registry, path safety, filesystem, memory, indexing, snapshots) uses only the Python standard library (`pathlib`, `dataclasses`, `json`, `re`, `time`, `uuid`, `shutil`, `abc`, `enum`) — confirmed by reading every core module. The stdlib-first philosophy claimed elsewhere in the docs holds up under inspection. |
| Obsidian vault detection | **PARTIALLY READY** | There is no active "scan common Obsidian vault locations" detection step found in the source. Vault location is configured explicitly via `vault_root`/`OHSC_VAULT_ROOT`, not auto-detected. `FilesystemBackend` does check for a `.obsidian` folder when *indexing* (`index_store.py` skips `.obsidian` internals) but that's exclusion logic, not discovery logic. |
| Obsidian desktop app control | **NOT READY / NOT IN SCOPE TODAY** | No code touches the Obsidian application itself (no local REST API client, no plugin bridge). All integration is direct markdown-file manipulation on disk. This is a legitimate, working, but *filesystem-only* integration — see `docs/OBSIDIAN_INTEGRATION.md`-equivalent content in `SYSTEM_OVERVIEW.md` / `context_README.md` for what already exists. |
| Graphify configuration | **PARTIALLY READY** | `ohsc/integrations/graphify/graphify_config.py` and `graphify_brain_config.py` exist and are read by the client/runner; the *external* `graphify` binary and `graphify-mcp` executable are optional dependencies that must be separately installed (not vendored, not auto-installed). Confirmed absent in this audit sandbox, and the gateway degrades gracefully rather than crashing when they're missing — that graceful-degradation behavior is itself READY. |
| API/LLM key handling | **READY (mechanism)** | `graphify_brain_config.py`/`graphify_brain_llm.py` reference an API key via environment variable naming (e.g. `OPENCODE_API_KEY`), not a hardcoded value — no key material found in the repo. Whether the *specific* backend (OpenCode) is the right long-term default is a product decision, not audited here. |
| Activation / health check (`ohsc activate`) | **READY** | `ohsc/gateway.py` implements an `activation_status()` function returning `ACTIVE`/`DEGRADED`/`BLOCKED`, exercised by `tests/test_gateway.py`. Confirmed working end-to-end in this sandbox — it correctly reported `DEGRADED` when Graphify/MCP binaries were absent, rather than failing hard. |
| Capability discovery for external agents | **READY** | `ohsc/capabilities.json` (duplicated at `capabilities/capabilities.json`, see GAP-003) is a structured, versioned manifest of architecture, capability groups and operations, consumed by the gateway. |
| Test isolation for install validation | **READY** | `tests/conftest.py` and the three synthetic vaults under `tests/graphify_brain_validation/` show the test suite already uses fixture vaults rather than a real one — safe to run repeatedly. |
| CI / automated install verification | **NOT READY** | No `.github/workflows/` directory exists in the repository at all today. |
| Manual configuration required today | **User must currently:** set `OHSC_SYSTEM_ROOT` and `OHSC_VAULT_ROOT` env vars (or edit `config/ohsc.json`) to override the Windows defaults; separately install `graphify`/`graphify-mcp` if Graphify features are wanted; and run from inside the repo directory since there's no installed package. |

## Overall verdict

The **core control-plane** (orchestrator/planner/workflow/registry/reviewer/
permissions/path-safety/memory/indexing/snapshots) is READY in the sense
that it is real, tested, stdlib-only, working code. What blocks the
"one-command install" vision is entirely at the **edges**: no packaging
metadata, Windows-only default paths, no CI, and no vault
auto-detection. None of these are architectural problems with OHSC
itself — they are the specific, addressable gaps a future installer
would need to close, and they're the same items already tracked in
`docs/GAPS.md` (GAP-001, GAP-002) plus the new packaging gap noted here.
