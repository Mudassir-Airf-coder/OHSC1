"""OHSC — Hermes Obsidian System Control.

A modular, autonomous, multi-agent control plane for managing an Obsidian
vault through natural-language requests.

Package layout:
    ohsc.core.*      -> shared infrastructure (safety, permissions, fs, logging,
                        validation, transactions, snapshots, indexing, memory,
                        registry, runtime, orchestrator, planner, workflow)
    ohsc.agents.*    -> specialized + safety + reviewer agents
    ohsc.skills.*    -> reusable procedures/knowledge
    ohsc.cli         -> command line entry point
"""

__version__ = "1.0.0"
__system_name__ = "Hermes Obsidian System Control"
__short_name__ = "OHSC"
