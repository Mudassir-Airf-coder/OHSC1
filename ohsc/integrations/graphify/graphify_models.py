"""Graphify data models used by OHSC.

These mirror the provenance distinction Graphify makes between EXTRACTED
(explicit, e.g. a wikilink the note actually contains) and INFERRED
(semantic, discovered by the model) relationships. OHSC preserves that
distinction so it never presents an inferred link as an explicit fact.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List


class EdgeKind(str, Enum):
    EXTRACTED = "extracted"   # explicit / structural relationship
    INFERRED = "inferred"     # semantic / discovered relationship


@dataclass
class GraphNode:
    id: str
    label: str
    kind: str = "concept"
    community: str = ""
    metadata: Dict[str, str] = field(default_factory=dict)


@dataclass
class GraphEdge:
    source: str
    target: str
    kind: EdgeKind = EdgeKind.INFERRED
    label: str = ""
    confidence: float = 1.0


@dataclass
class GraphAnalysis:
    nodes: List[GraphNode] = field(default_factory=list)
    edges: List[GraphEdge] = field(default_factory=list)
    communities: List[List[str]] = field(default_factory=list)
    hubs: List[str] = field(default_factory=list)
    orphans: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, object]:
        return {
            "nodes": [vars(n) for n in self.nodes],
            "edges": [
                {"source": e.source, "target": e.target,
                 "kind": e.kind.value, "label": e.label,
                 "confidence": e.confidence}
                for e in self.edges
            ],
            "communities": self.communities,
            "hubs": self.hubs,
            "orphans": self.orphans,
        }
