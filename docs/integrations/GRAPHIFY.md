# Graphify Integration

## Boundary

```text
OHSC graphify_agent
   ↓
GraphifyRunner
   ↓
GraphifyClient / Graphify Brain
   ↓
Graphify CLI or MCP interface
   ↓
Graph data + analysis
```

`GraphifyAgent` is the OHSC component that knows how Graphify works. It exposes four workflow actions: `build`, `query`, `shortest_path`, `explain`, and a structural `analyze` action.

## Build

`build` invokes the runner to create Graphify artifacts. The agent reports graph, HTML and report paths returned by the runner. The configured design is read-only against the user's vault; generated Graphify data belongs in the OHSC workspace.

## Query and analysis

- **query**: natural-language question over the built graph.
- **shortest_path**: conceptual path between two nodes.
- **explain**: explain a node's conceptual relationships/provenance.
- **analyze**: checks for an existing graph and returns its path/version through the current agent implementation.

The underlying Graphify integration also contains an MCP server module with graph-navigation tools. MCP is an optional interface; the validated gateway/CLI does not depend on MCP being available.

## Brain/backend

The repository contains `graphify_brain.py`, `graphify_brain_config.py`, and `graphify_brain_llm.py`. The current checked-in capability manifest describes the production backend as `opencode` with model `opencode/hy3-free`. Credentials are not part of the repository and must be supplied through the environment/configuration mechanism used by the implementation.

## Caching

`GraphifyRunner` is responsible for build/reuse behavior. The existing validation reported mtime/version-based reuse for unchanged graph input. Do not infer cache correctness from documentation alone; rerun the integration tests when changing the runner.

## Safety

Before Graphify execution, the agent verifies that the configured vault exists and has an `.obsidian` directory. The agent refuses an unconfigured/non-vault path. Graph artifacts are intended to stay outside the vault.

## Failure behavior

Unavailable Graphify is reported as `GRAPHIFY UNAVAILABLE`. Missing graphs are reported before graph-only analysis. Query/build errors are converted into structured `AgentResult` failures.

## Does not do

Graphify does not replace the Linking Agent. Explicit wikilinks and semantic/inferred relationships are separate concepts. Graphify also does not, by itself, prove desktop-application control of Obsidian.
