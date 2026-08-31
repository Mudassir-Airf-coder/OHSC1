# Installation Readiness

This is an audit, not an installer implementation.

| Component | Status | Evidence / limitation |
|---|---|---|
| Python source package | PARTIALLY READY | `ohsc/` is a coherent Python package, but no `pyproject.toml`, `setup.py`, or `requirements.txt` was found in the repository tree. |
| CLI/gateway | PARTIALLY READY | Repository contains `ohsc/cli.py`, `ohsc/gateway.py`, and launcher-related functionality documented by the existing agent skill. A fresh clone still needs the launcher/install environment to be established. |
| One-command activation | VERIFIED ON VALIDATED MACHINE | Existing validation reported `ohsc activate` working from arbitrary directories. This is not proof of fresh-clone installation on every machine. |
| Configuration | PARTIALLY READY | `config/ohsc.json` and environment-based secret handling exist; machine-local paths are present in the current configuration/manifest. |
| Obsidian vault | PARTIALLY READY | A configured vault root is required; automatic cross-machine discovery is not established by the checked-in repository alone. |
| Graphify | PARTIALLY READY | Graphify integration is implemented, but Graphify is an external dependency/runtime. |
| Graphify Brain / OpenCode | PARTIALLY READY | Existing configuration uses OpenCode + `opencode/hy3-free`; credentials and OpenCode installation are external prerequisites. |
| Graphify MCP | PARTIAL / OPTIONAL | MCP code exists, but previous validation reported missing `mcp`/`pywintypes` extras in the environment. |
| External AI agents | VERIFIED INTERFACE | CLI/gateway capability and agent discovery are documented; fresh-machine installation still needs packaging work. |
| Future one-command installer | NOT READY | A reproducible installer/configuration flow is not yet represented by packaging metadata. |

## Future target

```text
one command
  → install package
  → configure environment
  → discover/validate Obsidian vault
  → validate Graphify
  → validate OpenCode/Brain
  → activate gateway
  → expose capabilities to external agents
```

This repository-preparation task does not implement that future installer because doing so would exceed the requested documentation/organization scope.
