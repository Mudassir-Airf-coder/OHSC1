"""Graphify MCP adapter tests.

Verifies the MCP client exposes the relevant graph-navigation tools and
returns structured results. Skips if graphify-mcp is unavailable or no graph
exists yet.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from ohsc.integrations.graphify.graphify_mcp import GraphifyMCPClient, RELEVANT_TOOLS

FIXTURE_GRAPH = Path(r"D:\HOSC\tests\fixtures\fixture_graph.json")


def test_mcp_availability():
    if not GraphifyMCPClient(FIXTURE_GRAPH).is_available():
        pytest.skip("graphify-mcp executable not installed")


def test_relevant_tools_exclude_pr_tools():
    # PR tools are code-repo specific and must not be surfaced for vaults.
    assert "list_prs" not in RELEVANT_TOOLS
    assert "get_pr_impact" not in RELEVANT_TOOLS
    assert "query_graph" in RELEVANT_TOOLS
    assert "shortest_path" in RELEVANT_TOOLS


def test_mcp_get_node():
    if not FIXTURE_GRAPH.exists():
        pytest.skip("no fixture graph")
    mcp = GraphifyMCPClient(str(FIXTURE_GRAPH))
    if not mcp.is_available():
        pytest.skip("graphify-mcp unavailable")
    r = mcp.call("get_node", {"label": "OHSC"})
    assert r["ok"] is True
    assert "OHSC" in (r.get("answer") or "")


def test_mcp_shortest_path():
    if not FIXTURE_GRAPH.exists():
        pytest.skip("no fixture graph")
    mcp = GraphifyMCPClient(str(FIXTURE_GRAPH))
    if not mcp.is_available():
        pytest.skip("graphify-mcp unavailable")
    r = mcp.call("shortest_path", {"source": "OHSC", "target": "Obsidian", "undirected": True})
    assert r["ok"] is True
    assert "path" in (r.get("answer") or "").lower()


def test_mcp_unsupported_tool_rejected():
    mcp = GraphifyMCPClient(str(FIXTURE_GRAPH))
    r = mcp.call("list_prs", {})
    assert r["ok"] is False
