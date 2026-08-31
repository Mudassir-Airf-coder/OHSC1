# MCP Readiness

## What MCP means here

MCP (Model Context Protocol) is an optional tool interface for exposing capabilities to AI clients. In this repository, the Graphify integration contains `graphify_mcp.py`, while the validated Universal Agent Gateway is primarily CLI-based.

## Current implementation

The capability manifest lists Graphify MCP tools:

- `query_graph`
- `get_node`
- `get_neighbors`
- `god_nodes`
- `graph_stats`
- `shortest_path`
- `get_community`

The repository therefore contains MCP-related implementation, but that does not mean every environment can launch it.

## Readiness classification

**CLI gateway: VERIFIED.** The documented `ohsc` activation/discovery path is the primary validated external-agent interface.

**Graphify MCP: PARTIAL / OPTIONAL.** Earlier validation reported that the MCP server could not launch in the validation environment because required MCP/Windows Python extras were unavailable. Tests skip this optional integration honestly when the runtime dependency is absent.

## Fallback

When MCP is unavailable, external agents can use the CLI/gateway and its machine-readable capability and agent discovery interfaces. The repository must not describe MCP as mandatory unless the dependency becomes mandatory in packaging.

## Future use

The future Master MCP Generator may compose OHSC with other tools. This repository-preparation task does not implement that architecture; it only documents the current MCP boundary and readiness.
