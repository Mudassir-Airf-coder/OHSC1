"""Graphify vault-safety tests.

Confirms the Graphify integration never operates outside approved roots and
keeps all generated data out of any vault.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from ohsc.integrations.graphify.graphify_config import default_workspace


REAL_VAULT = Path(r"C:\Users\HAJI LAPTOP G55\Documents\Obsidian Vault")


def test_workspace_never_inside_real_vault():
    paths = default_workspace(Path(r"D:\HOSC"))
    for p in paths.values():
        assert not p.resolve().is_relative_to(REAL_VAULT)


def test_runner_writes_graph_outside_vault(tmp_path):
    from ohsc.integrations.graphify.graphify_runner import GraphifyRunner
    from ohsc.integrations.graphify.graphify_client import GraphifyClient
    v = tmp_path / "v"
    (v / ".obsidian").mkdir(parents=True)
    (v / "A.md").write_text("# A\n[[B]]\n")
    (v / "B.md").write_text("# B\n")
    runner = GraphifyRunner(Path(r"D:\HOSC"), client=GraphifyClient(), vault_root=v)
    gp = runner.graph_path()
    # Graph output location must resolve under D:\HOSC, never under the vault.
    assert gp.resolve().is_relative_to(Path(r"D:\HOSC"))
    assert not gp.resolve().is_relative_to(v)
