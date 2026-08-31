"""Graphify Agent tests: registration, vault safety, routing through the agent.

Uses a temporary vault and the OHSC runtime. Never touches the real vault.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from ohsc.system import build_runtime
from ohsc.config import SystemConfig
from ohsc.core.contracts import Task, OpClass, TaskStatus


@pytest.fixture
def rt_tmp(tmp_path):
    v = tmp_path / "vault"
    (v / ".obsidian").mkdir(parents=True)
    (v / "OHSC.md").write_text("# OHSC\n[[Graphify]]\n")
    (v / "Graphify.md").write_text("# Graphify\n")
    cfg = SystemConfig(system_root=Path(r"D:\HOSC"), vault_root=v,
                       allowed_roots=[Path(r"D:\HOSC"), v], safety_mode="strict")
    return build_runtime(cfg), v


def test_agent_registered(rt_tmp):
    rt, _ = rt_tmp
    ga = rt.registry.get("graphify_agent")
    assert ga is not None
    assert ga.role == "graph_intelligence"


def test_agent_refuses_unauthorized(rt_tmp):
    rt, _ = rt_tmp
    ga = rt.registry.get("graphify_agent")
    t = Task(agent="graphify_agent", action="build", op_class=OpClass.READ,
             authorized=False, params={"request": "b"})
    res = ga.execute(t)
    assert res.status == TaskStatus.FAILURE
    assert "UNAUTHORIZED" in res.summary


def test_agent_vault_mismatch_reports_mismatch():
    cfg = SystemConfig(system_root=Path(r"D:\HOSC"),
                       vault_root=Path(r"D:\NonexistentVaultXX"),
                       allowed_roots=[Path(r"D:\HOSC")], safety_mode="strict")
    rt = build_runtime(cfg)
    ga = rt.registry.get("graphify_agent")
    t = Task(agent="graphify_agent", action="build", op_class=OpClass.READ,
             authorized=True, params={"request": "b"})
    res = ga.execute(t)
    assert res.status == TaskStatus.FAILURE
    assert res.summary == "VAULT PATH MISMATCH"


def test_agent_read_only_does_not_modify_vault(rt_tmp):
    rt, v = rt_tmp
    ga = rt.registry.get("graphify_agent")
    before = {p.name for p in v.glob("*.md")}
    ga.execute(Task(agent="graphify_agent", action="analyze", op_class=OpClass.READ,
                    authorized=True, params={"request": "a"}))
    after = {p.name for p in v.glob("*.md")}
    # Analysis must not create/delete notes in the vault.
    assert before == after
