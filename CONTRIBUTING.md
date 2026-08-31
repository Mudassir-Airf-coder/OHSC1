# Contributing to OHSC

## Principle

Preserve the existing architecture. Prefer small, evidence-backed changes over rewrites.

## Development

1. Clone the repository.
2. Establish the Python environment required by the source and tests.
3. Run `python --version`.
4. Run `python -m pytest`.
5. Run `python -m compileall .`.
6. Verify CLI behavior where the local installation/launcher is available.

## Adding an agent

Implement a `BaseAgent` subclass, define an `AgentContract`, register it in `ohsc/system.py`, add tests, and update `docs/agents/AGENTS.md` plus the capability manifest after verification.

## Adding a skill

Document the skill's purpose, inputs, outputs, permissions, failure modes and examples. Keep agent-facing instructions operational and deterministic.

## Adding an integration

Keep external integrations behind a clear boundary. Document dependencies, configuration, health checks, fallback behavior, security implications, and whether the integration is optional.

## Tests

Do not weaken existing tests to make a change pass. Use isolated temporary vaults for filesystem validation. Never delete real user notes during tests.

## Documentation

Changes that affect commands, agents, capabilities, configuration, safety, integrations, or installation must update the relevant documentation.

## Security

Never commit secrets. Do not add credentials to fixtures, examples, logs, screenshots, or reports. Preserve path-safety and authorization boundaries.

## Pull requests

Describe what changed, why it was necessary, affected files, risk, verification performed, and any remaining gaps. Avoid claiming verification that was not actually executed.
