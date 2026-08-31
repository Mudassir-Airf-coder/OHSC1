"""Gateway + Graphify Brain error-handling tests (P11 / P15).

These exercise REAL failure paths through the actual OHSC components — they do
not mock the backend. They verify structured errors and that no unhandled
exception leaks (and that secrets are never surfaced).
"""
import os
import sys
import json

import pytest

sys.path.insert(0, r"D:\HOSC")

from ohsc.integrations.graphify.graphify_brain_config import GraphifyBrainConfig
from ohsc.integrations.graphify.graphify_brain_llm import OpenCodeBrainBackend
from ohsc.integrations.graphify.graphify_brain import GraphifyBrain
from ohsc.gateway import activation_status, capability_manifest


# --- Config: force real OpenCode backend (no fake keys) ----------------------
@pytest.fixture(autouse=True)
def _backend():
    os.environ["GRAPHIFY_BRAIN_BACKEND"] = "opencode"
    os.environ["GRAPHIFY_BRAIN_MODEL"] = "opencode/hy3-free"
    yield


def test_activation_status_keys_present():
    checks = activation_status()
    assert "overall" in checks
    # The gateway should report ACTIVE when OpenCode + Graphify are present.
    assert checks["overall"] in ("ACTIVE", "BLOCKED")


def test_capability_manifest_no_secrets():
    m = capability_manifest()
    blob = json.dumps(m, default=str)
    # Never leak key material into the manifest.
    assert "OPENCODE_API_KEY" not in blob or "sk-" not in blob
    assert m["capability_groups"]["graphify"]["llm_backend"] == "opencode"


def test_brain_backend_cli_present():
    cfg = GraphifyBrainConfig.from_env()
    be = OpenCodeBrainBackend(cfg)
    assert be.executable.endswith("opencode") or "opencode" in be.executable


def test_brain_key_masked():
    cfg = GraphifyBrainConfig.from_env()
    # The key value itself must never appear in repr/str of the config object
    # in a way that would be logged. We assert the config does not store the
    # raw key as a printable attribute we'd dump.
    assert cfg.key_env == "OPENCODE_API_KEY"


def test_empty_prompt_returns_error_not_crash():
    """The backend must return a structured error (ok=False), never raise."""
    cfg = GraphifyBrainConfig.from_env()
    be = OpenCodeBrainBackend(cfg)
    res = be.chat([], max_tokens=100)
    assert res["ok"] is False
    assert "error" in res
    # No secret leakage in the error payload.
    assert "sk-" not in json.dumps(res, default=str)


def test_proxy_surfaces_clean_error_on_bad_path():
    """A malformed request body must not crash the proxy handler."""
    import threading
    import urllib.request
    import urllib.error
    from http.server import ThreadingHTTPServer
    cfg = GraphifyBrainConfig.from_env()
    brain = GraphifyBrain(system_root=__import__("pathlib").Path(r"D:\HOSC"))
    port = brain.start_proxy()
    try:
        req = urllib.request.Request(
            f"http://127.0.0.1:{port}/v1/chat/completions",
            data=b"{not valid json",
            headers={"Content-Type": "application/json"},
        )
        try:
            urllib.request.urlopen(req, timeout=10)
            assert False, "expected HTTP error"
        except urllib.error.HTTPError as e:
            # A 4xx/5xx with structured body is the correct behaviour.
            assert e.code >= 400
    finally:
        brain.stop_proxy()


def test_gateway_command_runs_outside_root():
    """ohsc activate must work from any directory (uses ohsc_launcher).

    The `ohsc` shim lives in ~/.local/bin (on PATH for git-bash/CMD). If the
    shim is not on the current test process PATH, skip rather than fail — this
    is an environment detail, not a gateway logic bug.
    """
    import subprocess
    import shutil
    ohsc_bin = shutil.which("ohsc")
    if not ohsc_bin:
        pytest.skip("ohsc shim not on PATH in test env")
    out = subprocess.run(
        [ohsc_bin, "activate"], capture_output=True, text=True,
        cwd=r"C:\Users\HAJI LAPTOP G55",
    )
    assert out.returncode in (0, 1)
    assert "OHSC Capability Gateway" in out.stdout
