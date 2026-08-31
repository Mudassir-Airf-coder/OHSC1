"""Graphify routing tests: Planner must send graph requests to graphify_agent.

Uses the production INTENT_RULES (no real vault access needed).
"""

from __future__ import annotations

from pathlib import Path

import pytest

from ohsc.core.planner import PlannerAgent


@pytest.fixture
def planner():
    return PlannerAgent()


GRAPH_PHRASES = [
    "Analyze the knowledge graph of my vault",
    "Find the shortest path between OHSC and Loop Engineering",
    "Find relationships between these notes",
    "Find graph hubs",
    "Analyze communities in my vault",
    "Show graph connections around Graph Engineering",
    "Generate a knowledge graph report",
]


@pytest.mark.parametrize("phrase", GRAPH_PHRASES)
def test_graph_phrases_route_to_graphify(planner, phrase):
    plan = planner.plan(phrase, authorized=True)
    assert plan.tasks, f"no tasks planned for: {phrase}"
    assert plan.tasks[0].agent == "graphify_agent", (
        f"'{phrase}' routed to {plan.tasks[0].agent}, expected graphify_agent"
    )


def test_shortest_path_extracts_endpoints(planner):
    plan = planner.plan("Find the shortest path between OHSC and Loop Engineering",
                        authorized=True)
    t = plan.tasks[0]
    assert t.action == "shortest_path"
    assert t.params.get("source") == "OHSC"
    assert t.params.get("target") == "Loop Engineering"


def test_non_graph_request_not_routed_to_graphify(planner):
    plan = planner.plan("Create a note titled Hello", authorized=True)
    assert plan.tasks[0].agent != "graphify_agent"


def test_linking_request_still_routes_to_linking(planner):
    plan = planner.plan("Find orphan notes", authorized=True)
    assert plan.tasks[0].agent == "linking_agent"
