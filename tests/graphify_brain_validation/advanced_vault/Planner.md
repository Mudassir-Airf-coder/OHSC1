# Planner

The Planner is an agent component responsible for decomposing a user request into a sequence of operations. Within an [[AI Agent]] architecture, the Planner maps natural language intent to concrete agent actions, including routing graph-related requests to the [[Graphify]] integration.

The Planner works closely with the [[Orchestrator]], which executes the plan, and the [[Reviewer]], which validates the result. Planner decisions are informed by a [[Knowledge Graph]] of available capabilities and by [[Software Architecture]] principles.
