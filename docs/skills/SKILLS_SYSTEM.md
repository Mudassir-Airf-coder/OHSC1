# Skills System

The repository has two relevant concepts: the agent-facing `skills/` directory and implementation-side skill modules under `ohsc/skills/` when present.

## Agent-facing skills

`skills/OHSC_AGENT_SKILL.md` is the canonical operational manual for external coding/AI agents. It describes activation, capability discovery, agents, Graphify, MCP, permissions, safety, workflows and failure handling.

## Internal skills

The package-side `ohsc/skills/` namespace is part of the Python implementation. Do not merge it with the root `skills/` directory blindly. They serve different concerns when both exist: executable/internal implementation versus agent-facing operational instructions.

## Adding a skill

- Define its purpose and boundary.
- Specify inputs/outputs.
- Specify permissions and safety rules.
- Provide failure behavior.
- Add tests.
- Update the agent-facing documentation if an external agent must know about it.
- Keep the capability manifest synchronized with verified runtime capabilities.
