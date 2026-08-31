# CLI and Universal Gateway

## Activation

`ohsc activate` is the validated one-command activation entry point on the development/validation machine. The existing agent-facing skill documents cross-directory operation through the local launcher/shim.

## Discovery

```text
ohsc status --json
ohsc capabilities --json
ohsc agents --json
```

Use JSON discovery for programmatic integration.

## Natural-language orchestration

```text
ohsc "<request>"
```

The Orchestrator delegates to the Planner, Workflow Engine, Agent Registry, specialist agent(s), and Reviewer.

## Graphify

The gateway supports Graphify-oriented operations through the existing `--graphify` interface documented by the agent skill. Use discovery/status first and do not assume Graphify is installed on a fresh machine.

## Safety

Write/destructive actions must follow the authorization contract. Never use the CLI to bypass path safety or to target an unverified vault.

## External agents

The recommended sequence is:

```text
activate → status → capabilities → agents → execute → inspect result → verify
```
