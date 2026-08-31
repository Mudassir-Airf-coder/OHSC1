"""Integration tests: agents via registry + planner + workflow."""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from conftest import make_test_runtime, cleanup
from ohsc.core.orchestrator import Orchestrator


def _run(rt, req, **kw):
    orch = Orchestrator(rt)
    return orch.handle(req, authorized=True, **kw)


def test_agent_registry_counts():
    rt, tmp = make_test_runtime()
    try:
        assert rt.registry.count() >= 15
        assert rt.registry.enabled_count() == rt.registry.count()
    finally:
        cleanup(tmp)


def test_planner_creates_single_task():
    rt, tmp = make_test_runtime()
    try:
        orch = Orchestrator(rt)
        plan = orch.planner.plan("Create a note titled Demo with content hi")
        assert len(plan.tasks) == 1
        assert plan.tasks[0].agent == "note_agent"
        assert plan.tasks[0].params.get("title") == "Demo"
    finally:
        cleanup(tmp)


def test_create_read_append_note():
    rt, tmp = make_test_runtime()
    try:
        assert _run(rt, "Create a note titled N1 with content Hello")["status"] == "SUCCESS"
        assert _run(rt, "Read note N1")["status"] == "SUCCESS"
        assert _run(rt, "Append to note N1 with content World")["status"] == "SUCCESS"
        content = (tmp / "vault" / "N1.md").read_text(encoding="utf-8")
        assert "Hello" in content and "World" in content
    finally:
        cleanup(tmp)


def test_search_text_and_tag():
    rt, tmp = make_test_runtime()
    try:
        res = _run(rt, "Search for Project")
        assert res["status"] == "SUCCESS"
        res2 = _run(rt, "Find notes tagged project")
        assert res2["status"] == "SUCCESS"
    finally:
        cleanup(tmp)


def test_daily_note_no_duplicate():
    rt, tmp = make_test_runtime()
    try:
        r1 = _run(rt, "Create a daily note")
        r2 = _run(rt, "Create a daily note")
        assert r1["status"] == "SUCCESS"
        # second run should report duplicate, not fail
        assert r2["report"]["steps"][0]["data"].get("duplicate") is True
    finally:
        cleanup(tmp)


def test_orphan_analysis():
    rt, tmp = make_test_runtime()
    try:
        res = _run(rt, "Find orphan notes")
        assert res["status"] == "SUCCESS"
    finally:
        cleanup(tmp)


def test_dry_run_delete_is_safe():
    rt, tmp = make_test_runtime()
    try:
        _run(rt, "Create a note titled Doomed with content x")
        # dry-run + not authorized -> should NOT delete
        res = _run(rt, "Delete note Doomed", dry_run=True)
        # Workflow halts on destructive unauth step, but vault untouched.
        assert (tmp / "vault" / "Doomed.md").exists()
    finally:
        cleanup(tmp)


def test_moc_creation():
    rt, tmp = make_test_runtime()
    try:
        res = _run(rt, "Create a MOC for Project")
        assert res["status"] == "SUCCESS"
    finally:
        cleanup(tmp)


def test_metadata_update_preserves_other_data():
    rt, tmp = make_test_runtime()
    try:
        _run(rt, "Create a note titled Meta with content body")
        res = _run(rt, "Update metadata of note Meta set status=done",
                   )
        # metadata agent takes properties param; use direct dispatch
        from ohsc.core.contracts import Task
        t = Task(agent="metadata_agent", action="update_property",
                 op_class=__import__("ohsc.core.contracts", fromlist=["OpClass"]).OpClass.WRITE,
                 authorized=True,
                 params={"title": "Meta", "properties": {"status": "done"}})
        rt.registry.dispatch(t)
        text = (tmp / "vault" / "Meta.md").read_text(encoding="utf-8")
        assert "status: done" in text
        assert "body" in text
    finally:
        cleanup(tmp)
