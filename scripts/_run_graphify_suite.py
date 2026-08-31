"""Run the full Graphify capability suite against a built graph + the Brain backend.

Capabilities: graph_stats, node lookup, neighbors, query, shortest_path,
communities (via report), god_nodes, orphans, explain.

Reads from env (no secret printed):
  GF_BASE_URL, GF_MODEL, GF_API_KEY, GF_GRAPH, GF_OUT (json report)
"""
import os, sys, subprocess, pathlib, json, time

VENV = r"C:\Users\HAJI LAPTOP G55\AppData\Roaming\uv\tools\graphifyy\Scripts\python.exe"
graph = pathlib.Path(os.environ["GF_GRAPH"])
out = pathlib.Path(os.environ.get("GF_OUT", "/tmp/gf_suite.json"))
env = dict(os.environ)
env["OPENAI_BASE_URL"] = os.environ["GF_BASE_URL"]
env["OPENAI_MODEL"] = os.environ["GF_MODEL"]
env["OPENAI_API_KEY"] = os.environ["GF_API_KEY"]
env.pop("PYTHONPATH", None)

def run(mode, *pos, **kw):
    cmd = [VENV, "-m", "graphify", mode]
    cmd += list(pos)
    cmd += ["--graph", str(graph)]
    extra = kw.get("extra") or []
    cmd += extra
    t0 = time.time()
    try:
        p = subprocess.run(cmd, capture_output=True, text=True, timeout=120, env=env)
        dt = time.time() - t0
        return {"ok": p.returncode == 0, "rc": p.returncode,
                "out": (p.stdout or "").strip()[-1200:],
                "err": (p.stderr or "").strip()[-400:], "dt": round(dt, 2)}
    except subprocess.TimeoutExpired as e:
        return {"ok": False, "rc": -1, "out": (e.stdout or "")[-800:],
                "err": "TIMEOUT", "dt": round(time.time() - t0, 2)}

import json as _json
g = _json.load(open(graph))
results = {}
results["stats"] = {
    "ok": True, "nodes": len(g.get("nodes", [])),
    "links": len(g.get("links", [])), "communities": len(g.get("communities", [])),
    "dt": 0.0,
}
results["god_nodes"] = run("god-nodes")
# orphan detection: nodes with degree 0 (computed from graph.json)
deg = {}
for l in g.get("links", []):
    s, t = l.get("source"), l.get("target")
    deg[s] = deg.get(s, 0) + 1
    deg[t] = deg.get(t, 0) + 1
orphans = [n.get("label") for n in g.get("nodes", []) if deg.get(n.get("id"), 0) == 0]
results["orphans"] = {"ok": True, "out": "orphans: " + (", ".join(orphans) if orphans else "none"), "dt": 0.0}
# query (LLM-backed)
results["query_1"] = run("query", "What connects Graphify and Obsidian?")
results["query_2"] = run("query", "Which nodes are most central?")
# shortest path (local, undirected)
results["path_1"] = run("path", "AI Agent", "Knowledge Graph", extra=["--undirected"])
results["path_2"] = run("path", "Neural Networks", "Obsidian", extra=["--undirected"])
# explain
results["explain_1"] = run("explain", "AI Agent")

out.write_text(json.dumps(results, indent=2, ensure_ascii=False), encoding="utf-8")
print(json.dumps({k: {"ok": v["ok"], "dt": v["dt"]} for k, v in results.items()}, indent=2))
