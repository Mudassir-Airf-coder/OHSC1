"""Phase 10 — end-to-end OHSC integration test.

Builds a Runtime with vault_root pointed at the isolated basic_vault and the
Graphify workspace under D:\\HOSC\\graphify\\e2e_test (outside any real vault),
then exercises the REAL OHSC pipeline:

  Planner.plan(request) -> Task{agent=graphify_agent}
  graphify_agent.execute(task) -> Brain -> LLM -> graph.json -> query/shortest_path/explain

This uses the real agents, real Brain, real extraction backend. The real user
vault is NOT touched (vault_root is the temp basic_vault).
"""
import os, sys, json, pathlib, time

sys.path.insert(0, r"D:\HOSC")
os.environ["PYTHONPATH"] = ""  # avoid Hermes-venv pollution

from ohsc.core.planner import PlannerAgent
from ohsc.agents.graphify_agent import GraphifyAgent
from ohsc.core.runtime import Runtime

SYSTEM_ROOT = pathlib.Path(r"D:\HOSC")
BASIC = SYSTEM_ROOT / "tests" / "graphify_brain_validation" / "basic_vault"
E2E = SYSTEM_ROOT / "graphify" / "e2e_test"
E2E.mkdir(parents=True, exist_ok=True)

# point Brain backend at working OpenAI-compatible endpoint via env
os.environ["GRAPHIFY_BRAIN_PROVIDER"] = "openai"
os.environ["GRAPHIFY_BRAIN_ENDPOINT"] = "https://generativelanguage.googleapis.com/v1beta/openai/"
os.environ["GRAPHIFY_BRAIN_MODEL"] = "gemini-2.5-flash"
os.environ["GRAPHIFY_BRAIN_KEY_ENV"] = "GEMINI_KEY_1"

# minimal runtime config pointing at the temp vault
from ohsc.config import SystemConfig
cfg = SystemConfig(
    system_root=SYSTEM_ROOT,
    vault_root=BASIC,
    allowed_roots=[str(SYSTEM_ROOT), str(BASIC)],
)

rt = Runtime(config=cfg)
planner = PlannerAgent()

# Route + execute matrix
matrix = [
    ("Analyze the knowledge graph of this vault", "build"),
    ("Find the connections between Graphify and Obsidian", "query"),
    ("Find the shortest path between AI Agents and Knowledge Graph", "shortest_path"),
    ("Explain how Graphify connects to the AI agent architecture", "explain"),
]
results = []
for req, want_action in matrix:
    plan = planner.plan(req)
    t = plan.tasks[0]
    routed = t.agent == "graphify_agent" and t.action == want_action
    agent = GraphifyAgent(rt)
    t.authorized = True
    tgt = t
    res = agent.execute(tgt)
    results.append({
        "request": req, "routed_to": t.agent, "action": t.action,
        "routing_ok": routed, "exec_ok": res.status.name == "SUCCESS",
        "summary": (res.summary or "")[:120],
    })
    print(f"[{'OK' if routed else 'BADROUTE'}] {t.agent}/{t.action} exec={res.status.name} :: {req[:45]}")

all_ok = all(r["routing_ok"] and r["exec_ok"] for r in results)
print("\nOHSC INTEGRATION PIPELINE:", "PASS" if all_ok else "FAIL")
for r in results:
    print(f"  {r['request'][:55]} -> {r['routed_to']}/{r['action']} exec={r['exec_ok']}")

# keep e2e graph output for inspection; nothing else to clean
sys.exit(0 if all_ok else 1)
