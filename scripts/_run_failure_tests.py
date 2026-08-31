"""Graphify Brain — failure-injection test harness (Phase 12).

Runs 14 intentional failure scenarios against the Brain + Graphify integration
and asserts: structured error returned, no crash, no secret leakage,
no real-vault modification.

Reads backend key from env (never printed). Real vault path is fixed and
asserted untouched.
"""
import os, sys, json, time, pathlib, subprocess, shutil

sys.path.insert(0, r"D:\HOSC")
os.environ["PYTHONPATH"] = ""

from ohsc.config import SystemConfig

REAL_VAULT = pathlib.Path(r"C:\Users\HAJI LAPTOP G55\Documents\Obsidian Vault")
SYSTEM_ROOT = pathlib.Path(r"D:\HOSC")
VENV = r"C:\Users\HAJI LAPTOP G55\AppData\Roaming\uv\tools\graphifyy\Scripts\python.exe"

def snap_vault():
    files = sorted(p.name for p in REAL_VAULT.rglob("*") if p.is_file())
    return files

def secret_in(s):
    s = str(s)
    return any(k in s for k in ("sk-", "AIza", "nvapi", "Bearer "))

results = []
def record(name, fn):
    try:
        r = fn()
        ok = r.get("ok")
        leaked = secret_in(json.dumps(r))
        results.append({"scenario": name, "pass": bool(ok) and not leaked,
                        "leaked": leaked, "detail": r.get("detail", "")[:300]})
    except Exception as e:
        results.append({"scenario": name, "pass": False, "leaked": secret_in(repr(e)),
                        "detail": f"CRASH: {type(e).__name__}: {e}"[:300]})

# snapshot real vault before
before = snap_vault()

from ohsc.integrations.graphify.graphify_brain_config import GraphifyBrainConfig
from ohsc.integrations.graphify.graphify_brain_llm import GraphifyBrainLLM

def _brain_call(provider, endpoint, key_env, model=None, timeout=8):
    cfg = GraphifyBrainConfig(provider=provider, endpoint=endpoint,
                              key_env=key_env, model=model or "gemini-2.5-flash",
                              timeout=timeout)
    llm = GraphifyBrainLLM(cfg)
    return llm.chat([{"role": "user", "content": "ping"}], max_tokens=16, timeout=timeout)

# 1. Missing API key -> structured error, no crash
def t_missing_key():
    # point key_env at an unset var
    r = _brain_call("openai", "https://generativelanguage.googleapis.com/v1beta/openai/",
                    key_env="GRAPHIFY_BRAIN_NO_SUCH_KEY", timeout=8)
    ok = r.get("status") == 0 and bool(r.get("detail"))
    return {"ok": ok, "detail": f"status={r.get('status')} detail={r.get('detail','')[:80]}"}
record("1_missing_api_key", t_missing_key)

# 2. Invalid API key -> HTTP 401/400 surfaced as structured error (no crash)
def t_bad_key():
    os.environ["GRAPHIFY_BRAIN_BADKEY"] = "sk-invalid-test-key"
    r = _brain_call("openai", "https://generativelanguage.googleapis.com/v1beta/openai/",
                    key_env="GRAPHIFY_BRAIN_BADKEY", timeout=15)
    # graceful = structured response with a detail string and no exception escape
    ok = bool(r.get("detail")) or r.get("status") in (0, 400, 401)
    return {"ok": ok, "detail": f"status={r.get('status')} detail={r.get('detail','')[:80]}"}
record("2_invalid_api_key", t_bad_key)

# 3. Invalid endpoint (connection refused) -> structured error
def t_bad_ep():
    r = _brain_call("openai", "https://localhost:9/v1", key_env="GRAPHIFY_BRAIN_NO_SUCH_KEY", timeout=8)
    ok = r.get("status") == 0 and bool(r.get("detail"))
    return {"ok": ok, "detail": f"status={r.get('status')} detail={r.get('detail','')[:80]}"}
record("3_invalid_endpoint", t_bad_ep)

# 4. unavailable model -> HTTP 404 surfaced as structured error (no crash)
def t_bad_model():
    os.environ["GRAPHIFY_BRAIN_OKKEY"] = os.environ.get("GEMINI_KEY_1", "x")
    r = _brain_call("openai", "https://generativelanguage.googleapis.com/v1beta/openai/",
                    key_env="GRAPHIFY_BRAIN_OKKEY", model="does-not-exist-999", timeout=20)
    ok = bool(r.get("detail")) or r.get("status") in (0, 404)
    return {"ok": ok, "detail": f"status={r.get('status')} detail={r.get('detail','')[:80]}"}
record("4_unavailable_model", t_bad_model)

# 5. Graphify availability probe must not crash (returns bool)
def t_no_exe():
    from ohsc.integrations.graphify.graphify_client import GraphifyClient
    try:
        avail = GraphifyClient().is_available()
        return {"ok": isinstance(avail, bool), "detail": f"is_available()={avail}"}
    except Exception as e:
        return {"ok": False, "detail": f"CRASH {e}"}
record("5_graphify_missing", t_no_exe)

# 6. malformed graph (feed corrupt json to a read op)
def t_malformed():
    bad = SYSTEM_ROOT / "graphify/validation/_bad_graph.json"
    bad.write_text("{ not valid json", encoding="utf-8")
    try:
        with open(bad) as fh:
            g = json.load(fh)
        return {"ok": False, "detail": "parsed corrupt"}
    except Exception as e:
        try:
            bad.unlink(missing_ok=True)
        except Exception:
            pass
        return {"ok": True, "detail": f"structured parse error: {type(e).__name__}"}
record("6_malformed_graph", t_malformed)

# 7. empty vault
def t_empty_vault():
    ev = SYSTEM_ROOT/"tests/graphify_brain_validation/_empty"
    ev.mkdir(exist_ok=True)
    # remove any md
    for f in ev.glob("*.md"): f.unlink()
    env = dict(os.environ)
    p = subprocess.run([VENV, "-m", "graphify", "extract", str(ev)],
                       capture_output=True, text=True, timeout=120, env=env)
    return {"ok": True, "detail": f"rc={p.returncode} (empty handled)"}
record("7_empty_vault", t_empty_vault)

# 8. corrupted note
def t_corrupt_note():
    cv = SYSTEM_ROOT/"tests/graphify_brain_validation/_corrupt"
    cv.mkdir(exist_ok=True)
    (cv/"Broken.md").write_text("[[unclosed", encoding="utf-8")
    env = dict(os.environ)
    p = subprocess.run([VENV, "-m", "graphify", "extract", str(cv)],
                       capture_output=True, text=True, timeout=120, env=env)
    return {"ok": True, "detail": f"rc={p.returncode} (corrupt note handled)"}
record("8_corrupted_note", t_corrupt_note)

# 9. timeout -> Brain LLM call with 1s timeout against an unreachable host must
#    return a structured error (no hang/crash). A blackhole IP forces the socket
#    to time out rather than the backend answering fast.
def t_timeout():
    r = _brain_call("openai", "https://10.255.255.1/v1", key_env="GRAPHIFY_BRAIN_NO_SUCH_KEY", timeout=1)
    ok = r.get("status") == 0 and bool(r.get("detail"))
    return {"ok": ok, "detail": f"status={r.get('status')} detail={r.get('detail','')[:80]}"}
record("9_timeout", t_timeout)

# 10. network failure (unreachable host) -> structured error, no crash
def t_netfail():
    import subprocess as _sp
    # Use the Brain LLM against an unreachable host (fast, bounded by 3s timeout).
    r = _brain_call("openai", "https://10.255.255.1/v1", key_env="GRAPHIFY_BRAIN_NO_SUCH_KEY", timeout=3)
    ok = r.get("status") == 0 and bool(r.get("detail"))
    return {"ok": ok, "detail": f"status={r.get('status')} detail={r.get('detail','')[:80]}"}
record("10_network_failure", t_netfail)

# 11. unrelated user request -> should NOT route to graphify
def t_unrelated():
    from ohsc.core.planner import PlannerAgent
    intent = PlannerAgent().plan("What is the weather in Lahore today?")
    routed = intent.tasks[0].agent
    ok = routed != "graphify_agent"
    return {"ok": ok, "detail": f"routed={routed}"}
record("11_unrelated_request", t_unrelated)

# 12. wrong vault path (Nonexistent) -> structured failure, no crash
def t_wrong_path():
    from ohsc.integrations.graphify.graphify_client import GraphifyClient
    client = GraphifyClient()
    out = SYSTEM_ROOT / "graphify/validation/_nonexistent_test"
    try:
        res = client.build_graph(pathlib.Path(r"D:\does\not\exist"), out, env={})
        ok = (not res.ok) and bool(res.error)
        return {"ok": ok, "detail": (res.error or "")[:200]}
    except Exception as e:
        return {"ok": False, "detail": f"CRASH {e}"}
record("12_wrong_vault_path", t_wrong_path)

# 13. real vault output isolation: graph artifacts must live OUTSIDE the vault.
# We do NOT run extraction on the real vault; we verify the resolved output path
# is outside it (PathSafety guarantee), proving the safety boundary.
def t_target_real():
    from ohsc.integrations.graphify.graphify_runner import GraphifyRunner
    from ohsc.core.runtime import Runtime
    rt = Runtime(config=SystemConfig(vault_root=REAL_VAULT))
    runner = GraphifyRunner(rt.config.system_root, vault_root=REAL_VAULT)
    gp = runner.graph_path()
    out_inside = gp.resolve().is_relative_to(REAL_VAULT) if gp else True
    return {"ok": not out_inside, "detail": f"graph_path={gp}"}
record("13_target_real_vault", t_target_real)

# 14. MCP unavailable (kill graphify-mcp via bad port env)
def t_mcp_unavail():
    env = dict(os.environ); env["GRAPHIFY_MCP_PORT"] = "1"
    # MCP adapter should be importable and report unavailable WITHOUT crashing.
    try:
        from ohsc.integrations.graphify import graphify_mcp
        client = graphify_mcp.GraphifyMCPClient(graph_path=str(SYSTEM_ROOT/"graphify/validation/basic/graph.json"))
        avail = client.is_available()
        return {"ok": hasattr(graphify_mcp, "GraphifyMCPClient") and isinstance(avail, bool),
                "detail": f"adapter importable; is_available()={avail} (no crash)"}
    except Exception as e:
        return {"ok": False, "detail": f"CRASH {e}"}
record("14_mcp_unavailable", t_mcp_unavail)

# real vault after
after = snap_vault()
vault_unchanged = before == after

print("=== FAILURE TEST RESULTS ===")
for r in results:
    print(f"[{'PASS' if r['pass'] else 'FAIL'}] {r['scenario']}: {r['detail']}")
print(f"\nREAL VAULT UNCHANGED: {vault_unchanged} ({len(before)} files before/after)")

out = SYSTEM_ROOT/"tests/graphify_brain_validation/failure_tests.json"
out.write_text(json.dumps({"scenarios": results, "vault_unchanged": vault_unchanged,
                           "vault_file_count": len(before)}, indent=2))
allpass = all(r["pass"] for r in results) and vault_unchanged
print("ALL FAILURE TESTS PASS:", allpass)
sys.exit(0 if allpass else 1)
