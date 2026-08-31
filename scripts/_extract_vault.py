"""Phase 7 harness: real Graphify + OpenCode(HY3) extraction for one vault.

Usage: python scripts/_extract_vault.py <basic|intermediate|advanced>

Starts the Graphify Brain proxy (OpenCode CLI backend, HY3) and runs
GraphifyRunner.build() against the isolated test vault. Records real metrics.
Secrets are NEVER printed.
"""
import os
import sys
import time
import json
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from ohsc.integrations.graphify.graphify_brain import GraphifyBrain
from ohsc.integrations.graphify.graphify_runner import GraphifyRunner

VAULTS = {
    "basic": Path(r"D:\HOSC\validation\basic_vault"),
    "intermediate": Path(r"D:\HOSC\validation\intermediate_vault"),
    "advanced": Path(r"D:\HOSC\validation\advanced_vault"),
}

SYSTEM_ROOT = Path(r"D:\HOSC")


def main():
    name = sys.argv[1] if len(sys.argv) > 1 else "basic"
    vault = VAULTS[name]
    if not vault.exists():
        print(f"VAULT MISSING: {vault}")
        return 2

    # Force OpenCode + HY3 production backend.
    os.environ["GRAPHIFY_BRAIN_BACKEND"] = "opencode"
    os.environ["GRAPHIFY_BRAIN_MODEL"] = "opencode/hy3-free"

    brain = GraphifyBrain(system_root=SYSTEM_ROOT)
    print(f"[config] provider={brain.config.provider} model={brain.config.model} "
          f"key_present={brain.config.has_key()}")

    port = brain.start_proxy()
    print(f"[proxy] listening on :{port}")

    runner = GraphifyRunner(
        system_root=SYSTEM_ROOT,
        vault_root=vault,
        brain=brain,
    )
    # Direct graph output per-vault so they don't collide.
    out_dir = SYSTEM_ROOT / "graphify" / "graphs" / name
    runner.paths["graphs"] = out_dir
    out_dir.mkdir(parents=True, exist_ok=True)

    t0 = time.time()
    result = runner.build(force=True)
    dt = time.time() - t0
    brain.stop_proxy()

    print(f"[extract] elapsed={dt:.1f}s ok={result.ok} error={result.error}")
    if not result.ok:
        print("[extract] STDOUT:", (result.stdout or "")[:800])
        print("[extract] STDERR:", (result.stderr or "")[:800])
        return 1

    gpath = result.graph_path
    with open(gpath, encoding="utf-8") as f:
        g = json.load(f)
    nodes = g.get("nodes") or g.get("vertices") or []
    edges = g.get("edges") or g.get("relationships") or []
    comms = g.get("communities") or []
    print(f"[graph] nodes={len(nodes)} edges={len(edges)} communities={len(comms)}")
    print(f"[graph] path={gpath}")
    # Persist a small metrics file for the report.
    (SYSTEM_ROOT / f"graphify/graphs/{name}/METRICS.json").write_text(json.dumps({
        "vault": name, "elapsed_s": round(dt, 2),
        "nodes": len(nodes), "edges": len(edges), "communities": len(comms),
        "graph_path": str(gpath),
    }, indent=2), encoding="utf-8")
    print("RESULT: PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
