"""Graphify installation & availability tests.

Verifies Graphify is actually installed and usable. Skips gracefully (with a
clear mark) if the binary is missing so the rest of the suite still runs.
"""

from __future__ import annotations

import shutil

import pytest

from ohsc.integrations.graphify.graphify_client import GraphifyClient


@pytest.fixture(scope="module")
def client():
    return GraphifyClient()


def test_graphify_binary_detected(client):
    # Either the dedicated binary is on PATH, or we skip.
    if shutil.which("graphify") is None:
        pytest.skip("graphify binary not installed in this environment")
    assert client.is_available() is True


def test_graphify_version_reported(client):
    if not client.is_available():
        pytest.skip("graphify binary not installed")
    ver = client.version()
    # Version string must be non-empty and mention graphify.
    assert ver
    assert "graphify" in ver.lower()


def test_graphify_mcp_executable_present():
    # The MCP server must be present for MCP integration.
    assert shutil.which("graphify-mcp") is not None, "graphify-mcp executable missing"


def test_unavailable_binary_returns_failure():
    fake = GraphifyClient(graphify_bin=r"C:\nonexistent\graphify.exe")
    # build_graph must not raise; returns structured failure.
    res = fake.build_graph("x", "y")
    assert res.ok is False
