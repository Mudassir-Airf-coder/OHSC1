# Reviewer

The Reviewer is the quality gate of an [[AI Agent]] system. After the [[Orchestrator]] executes a plan, the Reviewer checks architecture, security, vault isolation, routing correctness, and whether the result actually satisfies the request.

The Reviewer validates outputs from the [[Graphify]] integration and the broader [[Knowledge Graph]] subsystem, ensuring no secret leakage and no unauthorized vault modification. It is the final arbiter before a result is returned to the user.
