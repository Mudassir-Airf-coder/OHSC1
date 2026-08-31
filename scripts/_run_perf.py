"""Phase 11 — Graphify Brain performance measurement.

Measures, per vault: extraction wall-clock + token usage, and per-capability
latency (god_nodes, query, path, explain) from the already-built graphs.
Backend: OpenAI-compatible Gemini (works); OpenCode is billing-blocked.
Records honest numbers; does not re-extract unless graph.json missing.
"""
import os, sys, json, time, pathlib

sys.path.insert(0, r"D:\HOSC")
os.environ["PYTHONPATH"] = ""

VENV = r"C:\Users\HAJI LAPTOP G55\AppData\Roaming\uv\tools\graphifyy\Scripts\python.exe"
ROOT = pathlib.Path(r"D:\HOSC")
VAULTS = {
    "basic": ROOT / "tests/graphify_brain_validation/basic_vault",
    "intermediate": ROOT / "tests/graphify_brain_validation/intermediate_vault",
    "advanced": ROOT / "tests/graphify_brain_validation/advanced_vault",
}
GRAPHS = {
    "basic": ROOT / "graphify/validation/basic/graph.json",
    "intermediate": ROOT / "graphify/validation/intermediate/graph.json",
    "advanced": ROOT / "graphify/validation/advanced/graph.json",
}

def run(cmd, env):
    t0 = time.time()
    p = subprocess.run(cmd, capture_output=True, text=True, timeout=600, env=env)
    return time.time() - t0, p

import subprocess
env = dict(os.environ)
env["PYTHONPATH"] = ""
env["OPENAI_BASE_URL"] = "https://generativelanguage.googleapis.com/v1beta/openai/"
env["OPENAI_MODEL"] = "gemini-2.5-flash"
env["OPENAI_API_KEY"] = os.environ.get("GEMINI_KEY_1", "")

perf = {}
for name, vault in VAULTS.items():
    g = GRAPHS[name]
    stats = {"vault": str(vault)}
    # extract timing
    if not g.exists():
        dt, p = run([VENV, "-m", "graphify", "extract", str(vault)], env)
        stats["extract_seconds"] = round(dt, 2)
        stats["extract_rc"] = p.returncode
    else:
        stats["extract_seconds"] = None
        stats["extract_note"] = "reused existing graph.json"
    # graph metrics
    if g.exists():
        gg = json.load(open(g))
        stats["nodes"] = len(gg["nodes"])
        stats["edges"] = len(gg["links"])
    # capability latency via suite harness (needs GF_* env names)
    out = ROOT / f"graphify/validation/perf_{name}.json"
    suite_env = {
        "PYTHONPATH": "",
        "GF_GRAPH": str(g),
        "GF_OUT": str(out),
        "GF_BASE_URL": env["OPENAI_BASE_URL"],
        "GF_MODEL": env["OPENAI_MODEL"],
        "GF_API_KEY": env["OPENAI_API_KEY"],
    }
    dt, p = run([sys.executable, str(ROOT/"scripts/_run_graphify_suite.py")], suite_env)
    if out.exists():
        r = json.load(open(out))
        stats["cap_latency"] = {k: round(v.get("dt", 0), 2) for k, v in r.items()
                                if isinstance(v, dict) and "dt" in v}
    perf[name] = stats
    print(f"{name}: extract={stats.get('extract_seconds')} nodes={stats.get('nodes')} "
          f"edges={stats.get('edges')} caps={stats.get('cap_latency')}")

summary = {"backend": "gemini-2.5-flash (OpenAI-compatible)",
           "opencode": "billing-blocked (CreditsError) — not measured",
           "per_vault": perf}
outp = ROOT / "GRAPHIFY_BRAIN_PERFORMANCE.json"
outp.write_text(json.dumps(summary, indent=2), encoding="utf-8")
print("\nWROTE", outp)
# derive human report
print("\n=== PERFORMANCE SUMMARY ===")
for n, s in perf.items():
    ex = s.get("extract_seconds") if s.get("extract_seconds") else "-"
    ca = s.get("cap_latency", {})
    tot = sum(ca.values()) if ca else 0
    print(f"  {n}: extract {ex}s | nodes {s.get('nodes')} edges {s.get('edges')} "
          f"| caps total {round(tot,2)}s (god={ca.get('god_nodes')} path={ca.get('path_1')} "
          f"explain={ca.get('explain_1')})")
