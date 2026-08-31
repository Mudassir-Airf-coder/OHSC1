"""Run the full Graphify Brain validation pipeline for ONE vault.

Steps per vault:
  1. graphify extract   -> graph.json (semantic extraction via Brain backend)
  2. graphify cluster-only -> GRAPH_REPORT.md + graph.html (community naming via LLM)
Outputs graph.json + report + html into <vault>/graphify-out, then copies the
key artifacts to <out_dir> for the OHSC workspace.

Reads from env (no secret printed):
  GF_BASE_URL, GF_MODEL, GF_API_KEY, GF_VAULT, GF_OUT_DIR, GF_LOG
"""
import os, sys, subprocess, pathlib, shutil, time, json

VENV = r"C:\Users\HAJI LAPTOP G55\AppData\Roaming\uv\tools\graphifyy\Scripts\python.exe"
vault = pathlib.Path(os.environ["GF_VAULT"])
out_dir = pathlib.Path(os.environ.get("GF_OUT_DIR", str(vault / "graphify-out")))
log_path = os.environ.get("GF_LOG", "/tmp/gf_vault.log")
out_dir.mkdir(parents=True, exist_ok=True)

env = dict(os.environ)
env["OPENAI_BASE_URL"] = os.environ["GF_BASE_URL"]
env["OPENAI_MODEL"] = os.environ["GF_MODEL"]
env["OPENAI_API_KEY"] = os.environ["GF_API_KEY"]
env.pop("PYTHONPATH", None)

t0 = time.time()
lines = []
def log(s):
    lines.append(s); print(s, flush=True)

# 1) extract
log(f"[extract] vault={vault}")
cmd = [VENV, "-m", "graphify", "extract", str(vault)]
try:
    proc = subprocess.run(cmd, capture_output=True, text=True, timeout=1200, env=env)
    rc = proc.returncode
except subprocess.TimeoutExpired as e:
    rc = -1
    proc = type("P", (), {"stdout": e.stdout or "", "stderr": e.stderr or "", "returncode": -1})()
log(f"[extract] rc={rc}")
log(proc.stdout.strip()[-1500:] if proc.stdout else "(no stdout)")
if proc.stderr:
    log("[extract stderr] " + proc.stderr.strip()[-800:])

src_out = vault / "graphify-out"
gp = src_out / "graph.json"
if not gp.exists():
    log("FATAL: graph.json not produced")
    pathlib.Path(log_path).write_text("\n".join(lines), encoding="utf-8")
    sys.exit(2)

# copy graph.json into OHSC workspace (only if destination differs)
if gp.resolve() != (out_dir / "graph.json").resolve():
    shutil.copy2(gp, out_dir / "graph.json")
else:
    log("[extract] graph.json already in target dir; skip copy")
log(f"[extract] nodes/edges from graph.json")

# 2) cluster-only -> report + html (needs LLM for community naming)
log("[cluster-only] generating GRAPH_REPORT.md + graph.html")
cmd2 = [VENV, "-m", "graphify", "cluster-only", str(vault)]
try:
    p2 = subprocess.run(cmd2, capture_output=True, text=True, timeout=600, env=env)
    log(f"[cluster-only] rc={p2.returncode}")
    if p2.stdout: log(p2.stdout.strip()[-800:])
    if p2.stderr: log("[cluster stderr] " + p2.stderr.strip()[-500:])
except subprocess.TimeoutExpired as e:
    log("[cluster-only] TIMEOUT")

for name in ("GRAPH_REPORT.md", "graph.html"):
    s = src_out / name
    if s.exists():
        shutil.copy2(s, out_dir / name)
        log(f"[copy] {name} -> {out_dir / name}")

dt = time.time() - t0
log(f"[done] total={dt:.1f}s")
pathlib.Path(log_path).write_text("\n".join(lines), encoding="utf-8")
print(f"TOTAL_SECONDS={dt:.1f}")
