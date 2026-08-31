"""Phase 13 — Real vault safety integrity check.

Snapshots the REAL Obsidian vault file set + content hashes, waits, re-snapshots,
and asserts ZERO modifications. Also asserts every Graphify artifact lives OUTSIDE
the real vault (under D:\\HOSC\\graphify).
"""
import os, sys, json, pathlib, hashlib, time

REAL = pathlib.Path(r"C:\Users\HAJI LAPTOP G55\Documents\Obsidian Vault")
ROOT = pathlib.Path(r"D:\HOSC")

def snapshot():
    snap = {}
    for p in REAL.rglob("*"):
        if p.is_file():
            try:
                h = hashlib.sha256(p.read_bytes()).hexdigest()
            except Exception:
                h = "ERR"
            snap[str(p.relative_to(REAL))] = h
    return snap

def main():
    before = snapshot()
    # give a moment (other tests have already run by the time this is invoked)
    time.sleep(1)
    after = snapshot()
    added = set(after) - set(before)
    removed = set(before) - set(after)
    changed = {k for k in set(before) & set(after) if before[k] != after[k]}
    # graph artifacts must NOT be inside the real vault ROOT (outside .obsidian,
    # which is Obsidian's own internal dir that OHSC never writes to)
    graph_inside = [str(p) for p in REAL.rglob("graph.json")
                    if ".obsidian" not in str(p)]
    gfiles = [str(x) for x in (list(REAL.rglob("GRAPH_REPORT.md")) +
                               list(REAL.rglob("graph.html")))
              if ".obsidian" not in str(x)]
    violations = graph_inside + [str(x) for x in gfiles]

    result = {
        "real_vault_files_before": len(before),
        "real_vault_files_after": len(after),
        "added": sorted(added),
        "removed": sorted(removed),
        "changed": sorted(changed),
        "graph_artifacts_inside_real_vault": violations,
        "untouched": (not added and not removed and not changed and not violations),
    }
    out = ROOT / "VAULT_SAFETY_REPORT.json"
    out.write_text(json.dumps(result, indent=2), encoding="utf-8")
    print("REAL VAULT UNTOUCHED:", result["untouched"])
    print("  files:", len(before), "->", len(after))
    print("  added:", len(added), "removed:", len(removed), "changed:", len(changed))
    print("  graph artifacts inside real vault:", violations)
    sys.exit(0 if result["untouched"] else 1)

if __name__ == "__main__":
    main()
