"""Graphify configuration & workspace isolation tests.

Confirms all Graphify system data lives under the OHSC workspace and NEVER
inside a vault.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from ohsc.integrations.graphify.graphify_config import (
    default_workspace, ensure_workspace, to_dict,
)
from ohsc.integrations.graphify.graphify_models import EdgeKind, GraphNode, GraphEdge


SYSTEM_ROOT = Path(r"D:\HOSC")


def test_workspace_paths_outside_vault():
    paths = default_workspace(SYSTEM_ROOT)
    vault = Path(r"C:\Users\HAJI LAPTOP G55\Documents\Obsidian Vault")
    for p in paths.values():
        # No graphify path may resolve inside the real vault.
        assert not p.resolve().is_relative_to(vault)
        assert p.resolve().is_relative_to(SYSTEM_ROOT)


def test_workspace_creatable():
    paths = ensure_workspace(SYSTEM_ROOT)
    for p in paths.values():
        assert p.exists() and p.is_dir()


def test_workspace_to_dict_serializable():
    d = to_dict(SYSTEM_ROOT)
    assert all(isinstance(v, str) for v in d.values())


def test_edge_provenance_distinction():
    extracted = GraphEdge("A", "B", kind=EdgeKind.EXTRACTED)
    inferred = GraphEdge("A", "B", kind=EdgeKind.INFERRED)
    assert extracted.kind != inferred.kind
    assert extracted.kind.value == "extracted"
    assert inferred.kind.value == "inferred"


def test_graph_node_model():
    n = GraphNode(id="n1", label="OHSC", community="X")
    assert n.label == "OHSC"
