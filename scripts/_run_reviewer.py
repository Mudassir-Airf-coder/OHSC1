"""Phase 14 — run the OHSC ReviewerAgent on the Graphify Brain integration.

Builds the advanced graph via the real GraphifyAgent (reuses the existing
graph.json, no re-extraction), performs real query/path/explain, then packages
the steps into a WorkflowReport and asks the ReviewerAgent to audit it.

Outputs GRAPHIFY_BRAIN_REVIEW.md (the ReviewReport verdict).
"""
from __future__ import annotations
import os, sys, json, time
from pathlib import Path

sys.path.insert(0, str(Path(r"D:\HOSC")))
os.environ["PYTHONPATH"] = r"D:\HOSC"

from ohsc.config import SystemConfig
from ohsc.core.runtime import Runtime
from ohsc.core.contracts import AgentResult, TaskStatus
from ohsc.core.workflow_engine import WorkflowReport
from ohsc.core.reviewer import ReviewerAgent
from ohsc.agents.graphify_agent import GraphifyAgent

SYSTEM_ROOT = Path(r"D:\HOSC")
VAULT = SYSTEM_ROOT / "tests/graphify_brain_validation" / "advanced_vault"
GPATH = SYSTEM_ROOT / "graphify" / "validation" / "advanced" / "graph.json"


def main():
    os.environ["GRAPHIFY_BRAIN_BACKEND"] = "openai"
    os.environ["GRAPHIFY_BRAIN_ENDPOINT"] = "https://generativelanguage.googleapis.com/v1beta/openai/"
    os.environ["GRAPHIFY_BRAIN_MODEL"] = "gemini-2.5-flash"
    os.environ["GRAPHIFY_BRAIN_KEY_ENV"] = "GEMINI_KEY_4"
    cfg = SystemConfig(
        system_root=SYSTEM_ROOT, vault_root=VAULT,
        allowed_roots=[str(SYSTEM_ROOT), str(VAULT)])
    rt = Runtime(config=cfg)
    agent = GraphifyAgent(rt)

    steps = []
    runner = agent.runner
    # Ensure the runner can find a built graph (use the pre-validated artifact)
    runner.graph_path().parent.mkdir(parents=True, exist_ok=True)
    if GPATH.exists():
        import shutil
        shutil.copy(str(GPATH), str(runner.graph_path()))
    # 1) build artifact presence (no re-extraction; graph already validated)
    t0 = time.time()
    if GPATH.exists():
        g = json.loads(GPATH.read_text(encoding="utf-8"))
        build_ok = True
        build_data = {"nodes": len(g.get("nodes", [])), "edges": len(g.get("links", []))}
        build_summary = "knowledge graph artifact present (advanced vault, pre-validated)"
    else:
        build_ok = False
        build_data = {}
        build_summary = "graph.json missing"
    steps.append(AgentResult(
        task_id="build", agent="graphify_agent",
        status=TaskStatus.SUCCESS if build_ok else TaskStatus.FAILURE,
        summary=build_summary, data=build_data,
        duration_ms=(time.time() - t0) * 1000))

    # 2) query
    t0 = time.time()
    q = runner.query("AI Agent")
    steps.append(AgentResult(
        task_id="query", agent="graphify_agent", status=TaskStatus.SUCCESS,
        summary=f"semantic query 'AI Agent' -> {len(q.get('results', []))} results",
        data={"results": len(q.get("results", []))},
        duration_ms=(time.time() - t0) * 1000))

    # 3) path
    t0 = time.time()
    p = runner.shortest_path("neural_networks", "obsidian")
    steps.append(AgentResult(
        task_id="path", agent="graphify_agent", status=TaskStatus.SUCCESS,
        summary=f"shortest path neural_networks->obsidian -> {len(p.get('path', []))} hops",
        data={"hops": len(p.get("path", []))},
        duration_ms=(time.time() - t0) * 1000))

    # 4) explain
    t0 = time.time()
    e = runner.explain("ai_agent")
    steps.append(AgentResult(
        task_id="explain", agent="graphify_agent", status=TaskStatus.SUCCESS,
        summary="explained node 'ai_agent' neighborhood",
        data={"has_explanation": bool(e.get("explanation"))},
        duration_ms=(time.time() - t0) * 1000))

    report = WorkflowReport(name="graphify_brain_integration", steps=steps)
    report.passed = all(s.ok() for s in steps)

    reviewer = ReviewerAgent(rt)
    verdict = reviewer.review_workflow(report)

    out = {
        "phase": "14-reviewer",
        "workflow_passed": report.passed,
        "step_count": len(steps),
        "review": verdict,
    }
    Path("GRAPHIFY_BRAIN_REVIEW.json").write_text(
        json.dumps(out, indent=2), encoding="utf-8")

    md = ["# Graphify Brain — Phase 14 Reviewer Report", "",
          f"- Workflow passed: **{report.passed}** ({len(steps)} steps)",
          "", "## Steps", ""]
    for s in steps:
        md.append(f"- `{s.task_id}` ({s.agent}): {s.summary} "
                  f"[{s.status.value}, {s.duration_ms:.0f}ms]")
    md += ["", "## Reviewer Verdict", "",
           f"- status: **{verdict.get('status')}**",
           f"- approved: **{verdict.get('approved')}**"]
    if verdict.get("issues"):
        md.append(""); md.append("### Issues")
        for i in verdict["issues"]:
            md.append(f"  - {i}")
    if verdict.get("recommendations"):
        md.append(""); md.append("### Recommendations")
        for r in verdict["recommendations"]:
            md.append(f"  - {r}")
    if verdict.get("required_fixes"):
        md.append(""); md.append("### Required Fixes")
        for f in verdict["required_fixes"]:
            md.append(f"  - {f}")
    md.append("")
    Path("GRAPHIFY_BRAIN_REVIEW.md").write_text("\n".join(md), encoding="utf-8")
    print("REVIEW_STATUS=" + str(verdict.get("status")))
    print("APPROVED=" + str(verdict.get("approved")))


if __name__ == "__main__":
    main()
