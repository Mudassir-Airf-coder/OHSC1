"""Graphify runner tests: build, incremental/caching, query, path.

Uses a self-contained temporary vault so the real vault is never touched.
Requires Graphify + an LLM key for the extract step; if unavailable the build
portion is skipped but query/path tests run against a fixture graph.
"""

from __future__ import annotations

import json
import os
import shutil
from pathlib import Path

import pytest

from ohsc.integrations.graphify.graphify_client import GraphifyClient
from ohsc.integrations.graphify.graphify_runner import GraphifyRunner

SYSTEM_ROOT = Path(r"D:\HOSC")
FIXTURE_GRAPH = SYSTEM_ROOT / "tests" / "fixtures" / "fixture_graph.json"


@pytest.fixture
def tmp_vault(tmp_path):
    v = tmp_path / "vault"
    (v / ".obsidian").mkdir(parents=True)
    notes = {
        "OHSC.md": "# OHSC\nLinks [[Graphify]] and [[Obsidian]].\n",
        "Graphify.md": "# Graphify\nReads from [[Obsidian]].\n",
        "Obsidian.md": "# Obsidian\nStores notes.\n",
        "Orphan.md": "# Orphan\nNothing links here.\n",
    }
    for name, body in notes.items():
        (v / name).write_text(body)
    return v


def test_runner_caching_reuses_graph(tmp_vault):
    # Seed a valid metadata record so the runner considers the existing
    # fixture graph current (this isolates the caching DECISION from the
    # extract step, which needs an LLM key). A real rebuild is covered
    # manually via the CLI.
    runner = GraphifyRunner(SYSTEM_ROOT, client=GraphifyClient(), vault_root=tmp_vault)
    if not FIXTURE_GRAPH.exists():
        pytest.skip("no fixture graph built yet")
    # Write meta claiming the fixture graph matches this vault's mtime.
    runner._write_meta("0.9.50", runner._vault_mtime(tmp_vault))
    assert runner.needs_rebuild() is False
    res = runner.build(force=False)
    assert res.ok is True
    assert "reused" in (res.stdout or "").lower()


def test_runner_query_against_fixture():
    if not FIXTURE_GRAPH.exists():
        pytest.skip("no fixture graph")
    runner = GraphifyRunner(SYSTEM_ROOT, client=GraphifyClient(),
                            vault_root=SYSTEM_ROOT, graphs_dir=FIXTURE_GRAPH.parent)
    r = runner.query("What is connected to OHSC?")
    assert r["ok"] is True
    assert "OHSC" in (r.get("answer") or "")


def test_runner_shortest_path_against_fixture():
    if not FIXTURE_GRAPH.exists():
        pytest.skip("no fixture graph")
    runner = GraphifyRunner(SYSTEM_ROOT, client=GraphifyClient(),
                            vault_root=SYSTEM_ROOT, graphs_dir=FIXTURE_GRAPH.parent)
    r = runner.shortest_path("OHSC", "Obsidian")
    assert r["ok"] is True
    assert "path" in (r.get("answer") or "").lower()


def test_runner_missing_graph_reports_not_built():
    runner = GraphifyRunner(SYSTEM_ROOT, client=GraphifyClient(), vault_root=SYSTEM_ROOT)
    # Point graph path at a missing file via direct client call.
    res = GraphifyClient().query("x", SYSTEM_ROOT / "graphify" / "graphs" / "nope.json")
    assert res.ok is False
    assert res.error == "GRAPH NOT BUILT"


# -- retry wrapper: transient failures are recovered, permanent ones surface ----
import subprocess
from ohsc.integrations.graphify import graphify_client as gc


class _FakeProc:
    def __init__(self, returncode, stdout="", stderr=""):
        self.returncode = returncode
        self.stdout = stdout
        self.stderr = stderr


def test_run_retries_then_succeeds_on_transient(monkeypatch):
    """First call: rc=1 + transient stdout. Second call: rc=0. _run returns ok."""
    calls = {"n": 0}
    def fake_run(cmd, *a, **kw):
        calls["n"] += 1
        if calls["n"] == 1:
            return _FakeProc(1, stdout='{"error":"Internal server error, try again"}')
        return _FakeProc(0, stdout="graph built")
    monkeypatch.setattr(gc.subprocess, "run", fake_run)
    monkeypatch.setattr(gc.time, "sleep", lambda _s: None)  # speed up
    client = GraphifyClient()
    proc = client._run(["graphify", "extract", str(SYSTEM_ROOT)])
    assert proc.returncode == 0
    assert calls["n"] == 2, f"expected 1 retry, saw {calls['n'] - 1} retries"


def test_run_does_not_retry_permanent_failures(monkeypatch):
    """Non-transient rc=1 -> no retry, surface immediately."""
    calls = {"n": 0}
    def fake_run(cmd, *a, **kw):
        calls["n"] += 1
        return _FakeProc(2, stderr="graphify: invalid arguments")
    monkeypatch.setattr(gc.subprocess, "run", fake_run)
    monkeypatch.setattr(gc.time, "sleep", lambda _s: None)
    client = GraphifyClient()
    proc = client._run(["graphify", "extract", str(SYSTEM_ROOT)])
    assert proc.returncode == 2
    assert calls["n"] == 1, "permanent error must not retry"


def test_run_retries_on_timeout(monkeypatch):
    """TimeoutExpired on first call -> retry, second call OK."""
    calls = {"n": 0}
    def fake_run(cmd, *a, **kw):
        calls["n"] += 1
        if calls["n"] == 1:
            raise subprocess.TimeoutExpired(cmd, timeout=10)
        return _FakeProc(0, stdout="graph built")
    monkeypatch.setattr(gc.subprocess, "run", fake_run)
    monkeypatch.setattr(gc.time, "sleep", lambda _s: None)
    client = GraphifyClient(timeout=10)
    proc = client._run(["graphify", "extract", str(SYSTEM_ROOT)])
    assert proc.returncode == 0
    assert calls["n"] == 2


def test_is_transient_stderr_and_stdout(monkeypatch):
    """Heuristic must detect transient markers in BOTH streams."""
    assert gc._is_transient(
        _FakeProc(1, stderr="HTTP 503 unavailable"), None) is True
    assert gc._is_transient(
        _FakeProc(1, stdout='{"err":"500 internal server error"}'), None) is True
    assert gc._is_transient(
        _FakeProc(2, stderr="bad arguments"), None) is False
    assert gc._is_transient(_FakeProc(0, stdout="ok"), None) is False
    assert gc._is_transient(None, subprocess.TimeoutExpired("x", 1)) is True


# -- circuit breaker: short-circuits sustained outages, recovers via half-open --


def test_breaker_opens_after_threshold_and_short_circuits(monkeypatch):
    """3 consecutive failed _run() -> breaker open -> next call within the
    cooldown window raises GraphifyUnavailable without invoking subprocess.run."""
    calls = {"n": 0}
    def fake_run(cmd, *a, **kw):
        calls["n"] += 1
        # Always transient failure with 3 retries each -> 3 calls per _run().
        return _FakeProc(1, stderr="HTTP 503 service unavailable")
    monkeypatch.setattr(gc.subprocess, "run", fake_run)
    monkeypatch.setattr(gc.time, "sleep", lambda _s: None)
    # Keep a meaningful cooldown so the short-circuit branch is exercised.
    monkeypatch.setattr(gc, "_BREAKER_COOLDOWN_S", 60.0)
    monkeypatch.setattr(gc, "_BREAKER_THRESHOLD", 3)
    # Freeze time so the cooldown window never elapses during the test.
    monkeypatch.setattr(gc.time, "time", lambda: 1000.0)
    client = GraphifyClient()
    for _ in range(3):
        proc = client._run(["graphify", "extract", str(SYSTEM_ROOT)])
        assert proc.returncode == 1
    assert calls["n"] == 9
    assert client.breaker.state == gc._BREAKER_OPEN
    # Next call is short-circuited: subprocess.run is NOT called again.
    with pytest.raises(gc.GraphifyUnavailable):
        client._run(["graphify", "extract", str(SYSTEM_ROOT)])
    assert calls["n"] == 9  # unchanged


def test_breaker_half_open_probe_success_closes(monkeypatch):
    """After cooldown, the next call is allowed as a probe; success closes."""
    calls = {"n": 0}
    fake_t = {"now": 1000.0}
    def fake_run(cmd, *a, **kw):
        calls["n"] += 1
        if calls["n"] <= 9:
            return _FakeProc(1, stderr="HTTP 503")
        return _FakeProc(0, stdout="ok")
    monkeypatch.setattr(gc.subprocess, "run", fake_run)
    monkeypatch.setattr(gc.time, "sleep", lambda _s: None)
    monkeypatch.setattr(gc, "_BREAKER_COOLDOWN_S", 30.0)
    monkeypatch.setattr(gc, "_BREAKER_THRESHOLD", 3)
    monkeypatch.setattr(gc.time, "time", lambda: fake_t["now"])
    client = GraphifyClient()
    for _ in range(3):
        client._run(["graphify", "extract", str(SYSTEM_ROOT)])
    assert client.breaker.state == gc._BREAKER_OPEN
    # Advance the clock past the cooldown to allow the half-open probe.
    fake_t["now"] += 31.0
    proc = client._run(["graphify", "extract", str(SYSTEM_ROOT)])
    assert proc.returncode == 0
    assert client.breaker.state == gc._BREAKER_CLOSED
    assert client.breaker.consecutive_failures == 0


def test_breaker_does_not_open_on_permanent_failures(monkeypatch):
    """Permanent (non-transient) errors must NOT count toward the threshold."""
    def fake_run(cmd, *a, **kw):
        return _FakeProc(2, stderr="graphify: invalid arguments")
    monkeypatch.setattr(gc.subprocess, "run", fake_run)
    monkeypatch.setattr(gc.time, "sleep", lambda _s: None)
    monkeypatch.setattr(gc, "_BREAKER_THRESHOLD", 3)
    client = GraphifyClient()
    for _ in range(10):
        client._run(["graphify", "extract", str(SYSTEM_ROOT)])
    assert client.breaker.state == gc._BREAKER_CLOSED
    assert client.breaker.consecutive_failures == 0


def test_breaker_resets_consecutive_failures_on_success(monkeypatch):
    """A success between failures must reset the consecutive counter."""
    calls = {"n": 0}
    def fake_run(cmd, *a, **kw):
        calls["n"] += 1
        # 2 transient failures (each 3 calls), then success.
        if calls["n"] <= 6:
            return _FakeProc(1, stderr="HTTP 503")
        return _FakeProc(0, stdout="ok")
    monkeypatch.setattr(gc.subprocess, "run", fake_run)
    monkeypatch.setattr(gc.time, "sleep", lambda _s: None)
    monkeypatch.setattr(gc, "_BREAKER_THRESHOLD", 3)
    client = GraphifyClient()
    client._run(["x"])  # fail #1
    client._run(["x"])  # fail #2
    assert client.breaker.consecutive_failures == 2
    client._run(["x"])  # success -> reset
    assert client.breaker.consecutive_failures == 0
    assert client.breaker.state == gc._BREAKER_CLOSED
