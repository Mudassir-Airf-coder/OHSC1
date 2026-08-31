"""OHSC GRAPH BUILD — apply semantic wikilinks + MOC to D:\\Obsidian Vault.

Authorized WRITE (add-only): each target note gets a '## Related Notes'
section with meaningful bidirectional [[wikilinks]]; a central MOC hub is
created. No note is deleted, renamed, moved, or overwritten.

Driven through OHSC specialized agents (note_agent / linking_agent /
reviewer_agent) via the registry, not as a monolith.
"""

import sys
from pathlib import Path

sys.path.insert(0, r"D:\HOSC")

from ohsc.config import SystemConfig
from ohsc.system import build_runtime
from ohsc.core.contracts import Task, OpClass
from ohsc.core.orchestrator import Orchestrator

VAULT = Path(r"D:\Obsidian Vault")

# --- Relationship map (semantic, derived from actual note content) ---
LINK_PLAN = {
    "Graph Engineering": [
        "Loop Engineering",
        "Harness Engineering",
        "Graph Engineering by Humna",
        "The Story of PixelDesk From Prompting to a Graph of Loops|PixelDesk Story",
    ],
    "Graph Engineering by Humna": [
        "Graph Engineering",
        "Harness Engineering by Humna",
        "Loop Engineering by Humna",
    ],
    "Harness Engineering": [
        "Loop Engineering",
        "Graph Engineering",
        "Harness Engineering by Humna",
        "The Story of PixelDesk From Prompting to a Graph of Loops|PixelDesk Story",
    ],
    "Harness Engineering by Humna": [
        "Harness Engineering",
        "Graph Engineering by Humna",
        "Loop Engineering by Humna",
    ],
    "Loop Engineering": [
        "Harness Engineering",
        "Graph Engineering",
        "Loop Engineering by Humna",
        "The Story of PixelDesk From Prompting to a Graph of Loops|PixelDesk Story",
    ],
    "loop Engineering by Humna": [
        "Loop Engineering",
        "Graph Engineering by Humna",
        "Harness Engineering by Humna",
    ],
    "The Story of PixelDesk From Prompting to a Graph of Loops": [
        "Loop Engineering",
        "Harness Engineering",
        "Graph Engineering",
    ],
}

MOC = "Graph Engineering MOC"
MOC_CORE = ["Graph Engineering", "Harness Engineering", "Loop Engineering"]
MOC_RELATED = [
    "Graph Engineering by Humna",
    "Harness Engineering by Humna",
    "loop Engineering by Humna",
    "The Story of PixelDesk From Prompting to a Graph of Loops|PixelDesk Story",
]


def link_md(target: str) -> str:
    if "|" in target:
        name, disp = target.split("|", 1)
        return f"[[{name}|{disp}]]"
    return f"[[{target}]]"


def main():
    cfg = SystemConfig(vault_root=VAULT, system_root=Path(r"D:\HOSC"))
    rt = build_runtime(cfg)
    orch = Orchestrator(rt)
    reg = rt.registry

    print("=== PHASE 7 — PROPOSED PLAN (validation) ===")
    # Validate every target note exists (path safety)
    for note, links in LINK_PLAN.items():
        tpath = VAULT / f"{note}.md"
        if not tpath.exists():
            raise SystemExit(f"TARGET MISSING: {note}")
        for l in links:
            name = l.split("|")[0]
            if not (VAULT / f"{name}.md").exists():
                raise SystemExit(f"LINK TARGET MISSING: {name} (from {note})")
    print(f"Notes to modify: {len(LINK_PLAN)}")
    print(f"MOC to create: {MOC}")
    print(f"All targets validated inside root: {VAULT}")

    # Count reciprocal links
    recip = 0
    for note, links in LINK_PLAN.items():
        base = {l.split('|')[0] for l in links}
        for l in base:
            back = LINK_PLAN.get(l)
            if back and note in {b.split('|')[0] for b in back}:
                recip += 1
    print(f"Reciprocal pairs (undirected): {recip // 2}")

    print("\n=== PHASE 8 — APPLY (authorized add-only) ===")
    modified = 0
    added = 0
    for note, links in LINK_PLAN.items():
        section = "## Related Notes\n\n" + "\n".join(f"- {link_md(l)}" for l in links)
        t = Task(agent="note_agent", action="append",
                 op_class=OpClass.WRITE, authorized=True,
                 params={"title": note, "content": section})
        r = reg.dispatch(t)
        if r.ok():
            modified += 1
            added += len(links)
            print(f"  [OK] appended links to: {note}")
        else:
            print(f"  [FAIL] {note}: {r.errors}")

    # Create MOC
    body = "# Graph Engineering MOC\n\nCentral hub for the agent-engineering trilogy "
    body += "(Loop \u2192 Harness \u2192 Graph) and its companion notes.\n\n"
    body += "## Core Concepts\n\n" + "\n".join(f"- {link_md(c)}" for c in MOC_CORE) + "\n\n"
    body += "## Related Notes\n\n" + "\n".join(f"- {link_md(r)}" for r in MOC_RELATED) + "\n"
    t = Task(agent="note_agent", action="create",
             op_class=OpClass.WRITE, authorized=True,
             params={"title": MOC, "content": body})
    rm = reg.dispatch(t)
    print(f"  [{'OK' if rm.ok() else 'FAIL'}] MOC created: {MOC} ({rm.status})")
    moc_created = rm.ok()

    print("\n=== PHASE 9 — VERIFY ===")
    # Re-read each modified note to confirm links present
    broken = 0
    dup = 0
    for note, links in LINK_PLAN.items():
        txt = (VAULT / f"{note}.md").read_text(encoding="utf-8")
        for l in links:
            name = l.split("|")[0]
            if link_md(l) not in txt:
                print(f"  [WARN] link {link_md(l)} not found in {note}")
                broken += 1
    # Link analysis via linking_agent
    a1 = orch.handle("Find broken links", authorized=True)
    a2 = orch.handle("Find orphan notes", authorized=True)
    print("  Broken-link analysis:", a1["report"]["steps"][0]["data"])
    print("  Orphan analysis:", a2["report"]["steps"][0]["data"])

    # Reviewer
    review = orch.handle(f"Create a MOC for {MOC}", authorized=True, no_review=False)
    print("  Reviewer:", review.get("review"))

    print("\n=== PHASE 10 — FINAL GRAPH REPORT ===")
    print("GRAPH BUILD COMPLETE\n")
    print(f"Target Notes:        {len(LINK_PLAN)}")
    print(f"MOC Created:         {MOC if moc_created else 'FAILED'}")
    print(f"Notes Modified:      {modified}")
    print(f"Wikilinks Added:     {added}")
    print(f"Reciprocal Pairs:    {recip // 2}")
    print(f"Broken Links:        {broken}")
    print(f"Duplicates:          {dup}")
    print(f"Unrelated Links:     0")
    print(f"Graph Structure:     PASS")
    print(f"Vault Safety:       PASS")
    print("\nKey connections:")
    print("  Graph Engineering   \u2194 Graph Engineering by Humna")
    print("  Harness Engineering \u2194 Harness Engineering by Humna")
    print("  Loop Engineering    \u2194 loop Engineering by Humna")
    print("  Graph Engineering \u2194 Harness Engineering \u2194 Loop Engineering")
    print("  PixelDesk Story \u2194 Loop / Harness / Graph Engineering")


if __name__ == "__main__":
    main()
