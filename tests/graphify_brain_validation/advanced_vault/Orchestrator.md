# Orchestrator

The Orchestrator is the execution engine of an [[AI Agent]] system. It takes a plan produced by the [[Planner]] and dispatches it to the appropriate agents — for example, sending knowledge-graph analysis to the [[Graphify]] integration and routing document edits to the note agent.

The Orchestrator maintains task state and failure handling, and hands results to the [[Reviewer]] for validation. Its routing logic relies on the capability [[Knowledge Graph]] built by the [[Graph Engineering]] layer.
