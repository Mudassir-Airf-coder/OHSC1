# OHSC — Hermes Obsidian System Control

OHSC is a Python control plane for safe, structured operations over an Obsidian vault. It combines a planner, orchestrator, workflow engine, agent registry, safety/permission controls, indexing, memory, review, and Graphify-based semantic graph intelligence.

## What it does

- Inspects and validates an Obsidian vault.
- Creates, reads, updates, appends, renames, and deletes notes through specialized agents.
- Searches by text, tags, properties, filenames, folders, and links.
- Manages folders, links, metadata, templates, periodic notes, Canvas, dashboards/MOCs, and bulk operations through registered agents.
- Builds and queries a semantic knowledge graph through Graphify.
- Exposes a cross-directory `ohsc` gateway for external CLI coding/AI agents.
- Provides machine-readable capability discovery.
- Applies permission, path-safety, snapshot/transaction, validation, audit, and reviewer layers.

## Architecture

```text
User / External AI Agent
        ↓
CLI / Gateway
        ↓
Orchestrator
        ↓
Planner
        ↓
Workflow Engine
        ↓
Agent Registry
        ↓
Specialized Agents
   ↙        ↓        ↘
Obsidian  Graphify   Core services
Vault     + Brain    safety/index/memory
        ↓
Validation / Reviewer
        ↓
Structured Result / Audit
```

The implementation is the source of truth. See [`docs/architecture/ARCHITECTURE.md`](docs/architecture/ARCHITECTURE.md).

## Current interfaces

The repository currently exposes a CLI/gateway interface. The capability manifest describes `ohsc activate`, status/capability/agent discovery, natural-language orchestration, and Graphify operations. Graphify's MCP server is present in the source tree but is an optional interface and may require its external SDK/runtime dependencies; the CLI remains the validated fallback.

## Requirements

- Python: use the version supported by the checked-in runtime/package metadata; this repository currently does not contain `pyproject.toml`, `setup.py`, or `requirements.txt`, so installation metadata is a readiness gap.
- Graphify is required for Graphify features.
- The Graphify Brain production configuration uses the existing OpenCode-compatible backend and model configuration; credentials must be supplied through environment variables and must never be committed.

## Configuration

The checked-in capability manifest documents the current environment-oriented configuration, including the Graphify Brain backend and model. Do not copy local vault paths or secrets into source control. See [`docs/installation/INSTALLATION_READINESS.md`](docs/installation/INSTALLATION_READINESS.md).

## CLI

The validated gateway concept is:

```text
ohsc activate
ohsc status --json
ohsc capabilities --json
ohsc agents --json
ohsc "<natural-language request>"
```

Use the repository's launcher/install mechanism documented in [`docs/operations/CLI.md`](docs/operations/CLI.md). Do not assume a global installation exists merely because a local development machine has a shim.

## Obsidian

OHSC operates on the vault filesystem. It does not claim to control the Obsidian desktop application unless a separate integration proves that behavior. Vault writes are governed by path safety and permissions; Graphify analysis is read-only against the vault and writes generated artifacts to the OHSC workspace.

## Graphify

Graphify provides semantic graph construction and graph intelligence such as queries, paths, explanations, communities, hubs, and orphan analysis. The Graphify Brain supplies LLM-assisted semantic extraction. See [`docs/integrations/GRAPHIFY.md`](docs/integrations/GRAPHIFY.md).

## External AI agents

An external coding agent can discover the system through the gateway, inspect the capability manifest and agent registry, then invoke supported CLI operations. The canonical operational instructions are [`skills/OHSC_AGENT_SKILL.md`](skills/OHSC_AGENT_SKILL.md).

## Security

Never commit API keys, tokens, `.env` files, credentials, private keys, or local vault data. Destructive operations require explicit authorization. Test against isolated temporary vaults. See [`SECURITY.md`](SECURITY.md).

## Testing

The source repository contains an existing test suite. Run:

```text
python --version
python -m pytest
python -m compileall .
```

For a fresh clone, first verify that the required test/runtime dependencies are actually available; packaging metadata is currently incomplete.

## Project structure

```text
ohsc/                 Core package, agents, gateway and integrations
capabilities/         Machine-readable capability manifest
config/               Checked-in non-secret configuration
docs/                 Architecture, integrations, installation and reports
skills/               Agent-facing operational skill documentation
graphify/             Graphify Brain/client/MCP integration modules
tests/                Automated tests
bin/                  Repository-local binary material (review before distribution)
```

## Status

See [`docs/PROJECT_STATUS.md`](docs/PROJECT_STATUS.md) and [`docs/GAPS.md`](docs/GAPS.md). This repository-preparation pass deliberately documents gaps instead of silently redesigning the working system.

## License

MIT. See [`LICENSE`](LICENSE).
