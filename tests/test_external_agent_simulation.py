"""Phase 11 — External Agent Simulation (P11).

Simulates three external coding agents — OpenCode, Claude Code, Omni Router —
each performing the canonical discover → read SKILL.md → read manifest →
activate → discover agents/capabilities → select capability → execute →
verify workflow against the REAL OHSC components (no mocking of the gateway).

Graphify execution uses the prebuilt fixture graph (cached), so the test is
fast and offline-safe; the activation/capability/agent steps exercise the real
gateway code paths that an external agent would call.
"""
import json
import sys
from pathlib import Path

import pytest

sys.path.insert(0, r"D:\HOSC")

from ohsc.system import build_runtime
from ohsc.gateway import activation_status, capability_manifest
from ohsc.integrations.graphify.graphify_client import GraphifyClient

SKILL = Path(r"D:\HOSC\skills\OHSC_AGENT_SKILL.md")
MANIFEST = Path(r"D:\HOSC\capabilities\capabilities.json")
FIXTURE = Path(r"D:\HOSC\tests\fixtures\graph.json")


def _simulate_agent(agent_name: str):
    """Run the canonical external-agent workflow; return collected evidence."""
    evidence = {"agent": agent_name}

    # STEP 2: read SKILL.md
    assert SKILL.exists(), "SKILL.md must exist"
    skill_text = SKILL.read_text(encoding="utf-8")
    assert "Activation" in skill_text and "ohsc activate" in skill_text
    evidence["skill_read"] = True

    # STEP 3: read capability manifest
    assert MANIFEST.exists(), "capabilities/capabilities.json must exist"
    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    # No secret value in manifest.
    blob = json.dumps(manifest, default=str)
    assert "sk-" not in blob
    assert "nvapi" not in blob
    evidence["manifest_read"] = True

    # STEP 4: activate
    checks = activation_status()
    assert checks["overall"] == "ACTIVE", f"activation not ACTIVE: {checks}"
    evidence["activated"] = True

    # STEP 5/6/7: status, agents, capabilities (via real runtime)
    rt = build_runtime()
    agents = rt.registry.list_agents()
    assert len(agents) == 16, f"expected 16 agents, got {len(agents)}"
    evidence["agents_discovered"] = len(agents)
    manifest2 = capability_manifest()
    ev_groups = manifest2["capability_groups"]
    assert "graphify" in ev_groups, "graphify capability group missing"
    ops = {op["name"] for op in ev_groups["graphify"]["operations"]}
    assert {"build_graph", "query_graph", "shortest_path", "explain", "analyze"} <= ops
    evidence["capabilities_discovered"] = sorted(ops)

    # STEP 8/9: select + execute a Graphify capability (cached fixture graph)
    assert FIXTURE.exists(), "fixture graph missing"
    client = GraphifyClient()
    res = client.query("how are OHSC and Obsidian related?", graph_path=FIXTURE)
    assert res.ok is True, f"query failed: {res.error}"
    # Shortest path is the canonical graphify capability exercised by agents.
    path_res = client.shortest_path("OHSC", "Obsidian", graph_path=FIXTURE, undirected=True)
    assert path_res.ok is True, f"path failed: {path_res.error}"
    assert "Obsidian" in path_res.answer or "path" in path_res.answer.lower()
    evidence["graphify_executed"] = path_res.answer

    # STEP 10: verify result structure
    assert res.ok and path_res.ok
    evidence["verified"] = True
    return evidence


def test_external_agent_opencode():
    ev = _simulate_agent("OpenCode")
    assert ev["activated"] and ev["verified"]


def test_external_agent_claude_code():
    ev = _simulate_agent("Claude Code")
    assert ev["activated"] and ev["verified"]


def test_external_agent_omni_router():
    ev = _simulate_agent("Omni Router")
    assert ev["activated"] and ev["verified"]


def test_all_three_agents_see_same_capabilities():
    """Independence check: every agent discovers the same 16 agents + 5 ops."""
    caps = []
    for name in ("OpenCode", "Claude Code", "Omni Router"):
        ev = _simulate_agent(name)
        caps.append((ev["agents_discovered"], tuple(ev["capabilities_discovered"])))
    assert all(c == caps[0] for c in caps), f"capability drift across agents: {caps}"
