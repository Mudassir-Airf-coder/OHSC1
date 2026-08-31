"""End-to-end tests simulating realistic user requests (Phase 5 scenarios).

All run against an isolated test vault. The real vault is never touched.
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from conftest import make_test_runtime, cleanup
from ohsc.core.orchestrator import Orchestrator
from ohsc.core.contracts import Task, OpClass
from ohsc.core.reviewer import ReviewerAgent


def _run(rt, req, **kw):
    return Orchestrator(rt).handle(req, authorized=True, **kw)


def test_e2e_20_scenarios():
    rt, tmp = make_test_runtime()
    vault = tmp / "vault"
    try:
        # 1 create note
        assert _run(rt, "Create a note titled S1 with content alpha")["status"] == "SUCCESS"
        # 2 read note
        assert _run(rt, "Read note S1")["status"] == "SUCCESS"
        # 3 append
        assert _run(rt, "Append to note S1 with content beta")["status"] == "SUCCESS"
        # 4 update
        assert _run(rt, "Create a note titled S2 with content old")["status"] == "SUCCESS"
        t = Task(agent="note_agent", action="update", op_class=OpClass.WRITE,
                 authorized=True, params={"title": "S2", "content": "new"})
        assert rt.registry.dispatch(t).ok()
        # 5 search notes
        assert _run(rt, "Search for alpha")["status"] == "SUCCESS"
        # 6 search by tag
        assert _run(rt, "Find notes tagged project")["status"] == "SUCCESS"
        # 7 search by property
        assert _run(rt, "Search for Project")["status"] == "SUCCESS"
        # 8 create folder
        assert _run(rt, "Create folder Projects")["status"] == "SUCCESS"
        assert (vault / "Projects").is_dir()
        # 9 move note
        _run(rt, "Create a note titled M1 with content m")
        assert _run(rt, "Move note M1 to Projects")["status"] == "SUCCESS"
        # 10 rename note
        _run(rt, "Create a note titled Old with content o")
        t = Task(agent="note_agent", action="rename", op_class=OpClass.WRITE,
                 authorized=True, params={"title": "Old", "new_title": "New"})
        assert rt.registry.dispatch(t).ok()
        # 11 analyze links
        assert _run(rt, "Find broken links")["status"] == "SUCCESS"
        # 12 detect orphans
        assert _run(rt, "Find orphan notes")["status"] == "SUCCESS"
        # 13 create MOC
        assert _run(rt, "Create a MOC for Python")["status"] == "SUCCESS"
        # 14 create daily note
        assert _run(rt, "Create a daily note")["status"] == "SUCCESS"
        # 15 modify metadata
        _run(rt, "Create a note titled MetaX with content b")
        t = Task(agent="metadata_agent", action="update_property", op_class=OpClass.WRITE,
                 authorized=True, params={"title": "MetaX", "properties": {"k": "v"}})
        assert rt.registry.dispatch(t).ok()
        # 16 safe bulk operation
        _run(rt, "Create a note titled B1 with content x")
        _run(rt, "Create a note titled B2 with content x")
        t = Task(agent="bulk_agent", action="bulk_append", op_class=OpClass.WRITE,
                 authorized=True,
                 params={"selector": {"contains": "B"}, "op": {"content": "TAG"}})
        assert rt.registry.dispatch(t).ok()
        # 17 dry-run
        res = _run(rt, "Delete note S1", dry_run=True)
        assert (vault / "S1.md").exists()  # not actually deleted
        # 18 validation triggered (invalid note name)
        t = Task(agent="note_agent", action="create", op_class=OpClass.WRITE,
                 authorized=True, params={"title": "bad/name"})
        r = rt.registry.dispatch(t)
        assert not r.ok()
        # 19 reviewer triggered
        orch = Orchestrator(rt)
        res = orch.handle("Create a note titled Rev with content r")
        assert res["review"]["approved"] is True
        # 20 intentional failure -> handled gracefully
        t = Task(agent="note_agent", action="read", op_class=OpClass.READ,
                 params={"title": "DoesNotExist"})
        r = rt.registry.dispatch(t)
        assert not r.ok() and r.status.value == "FAILURE"
        print("ALL 20 E2E SCENARIOS PASSED")
    finally:
        cleanup(tmp)


def test_reviewer_rejects_failed_workflow():
    rt, tmp = make_test_runtime()
    try:
        reviewer = ReviewerAgent(rt)
        # Build a fake failed report-like object
        class Step:
            def ok(self): return False
            status = __import__("ohsc.core.contracts", fromlist=["TaskStatus"]).TaskStatus.FAILURE
            agent = "note_agent"; task_id = "x"; summary = "boom"; errors = ["e"]
        class Report:
            passed = False
            steps = [Step()]
        out = reviewer.review_workflow(Report())
        assert out["status"] == "FAIL"
        assert out["approved"] is False
        assert out["required_fixes"]
    finally:
        cleanup(tmp)
