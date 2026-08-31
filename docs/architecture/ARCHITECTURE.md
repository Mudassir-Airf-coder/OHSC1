# OHSC Architecture

## Source-of-truth principle

The implementation is authoritative. This document records the architecture observed in the repository; it does not redesign it.

## Request lifecycle

```text
Request
  ↓
CLI / Gateway
  ↓
Orchestrator.handle()
  ↓
PlannerAgent.plan()
  ↓
WorkflowEngine.run()
  ↓
AgentRegistry.dispatch()
  ↓
Specialized agent
  ↓
Filesystem / Graphify / core service
  ↓
Workflow report
  ↓
ReviewerAgent.review_workflow()
  ↓
Memory + structured result
```

The Orchestrator source explicitly describes itself as the central controller and delegates real work to specialist agents. The AgentRegistry is the runtime source of truth for registered agents.

## Core

- **Configuration**: runtime configuration supplies system root, vault root and feature settings.
- **Contracts**: `Task`, `AgentResult`, statuses and operation classes provide structured workflow boundaries.
- **Permissions**: READ/WRITE/DESTRUCTIVE classification is used by planning and agents; destructive note deletion requires explicit authorization.
- **Path safety**: vault paths are checked against allowed roots and safe joins are used for note paths.
- **Filesystem backend**: vault operations are routed through the backend abstraction rather than arbitrary direct file manipulation.
- **Logging/audit**: agents use the common logger and event recording path.
- **Snapshots/transactions**: snapshot and transaction agents are registered as infrastructure services for protected workflows.
- **Index**: the search subsystem can refresh an index and use it for fast search.
- **Memory**: successful request patterns are appended to the `history/requests` namespace by the Orchestrator.
- **Planner**: keyword/rule-based intent routing creates `Task` objects and extracts parameters.
- **Workflow Engine**: executes a `WorkflowPlan` and produces a `WorkflowReport`.
- **Orchestrator**: plans, executes, reviews, records successful request history, and returns a structured response.
- **Reviewer**: validates workflow results after execution.

## Agent registry

`ohsc/system.py` registers 16 runtime agents: four safety/infrastructure agents (permission, snapshot, transaction, reviewer) and twelve specialized agents (vault, note, search, folder, linking, metadata, template, periodic, canvas, dashboard, bulk, graphify).

## Graphify boundary

Graphify is isolated behind `GraphifyAgent`. The agent owns graph extraction and semantic graph operations; the Linking Agent remains responsible for explicit Obsidian wikilinks. Graphify analysis reads the configured vault and writes generated artifacts to the OHSC Graphify workspace.

## Safety boundary

The system distinguishes vault filesystem access from the Obsidian desktop application. No desktop-control claim is made by the current source. Graphify operations are documented as read-only against the vault.
