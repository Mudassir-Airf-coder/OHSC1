"""OHSC Graphify integration package.

Exposes the adapter layer so agents import via:

    from ohsc.integrations.graphify import (
        GraphifyClient, GraphifyRunner, GraphifyMCPClient,
        default_workspace, EdgeKind, GraphAnalysis,
    )

The Graphify Agent itself lives in ``ohsc.agents.graphify_agent``.
"""

from __future__ import annotations

from .graphify_client import GraphifyClient, GraphBuildResult, GraphQueryResult
from .graphify_runner import GraphifyRunner
from .graphify_mcp import GraphifyMCPClient, RELEVANT_TOOLS
from .graphify_config import default_workspace, ensure_workspace, to_dict
from .graphify_models import EdgeKind, GraphNode, GraphEdge, GraphAnalysis

__all__ = [
    "GraphifyClient", "GraphBuildResult", "GraphQueryResult",
    "GraphifyRunner", "GraphifyMCPClient", "RELEVANT_TOOLS",
    "default_workspace", "ensure_workspace", "to_dict",
    "EdgeKind", "GraphNode", "GraphEdge", "GraphAnalysis",
]
