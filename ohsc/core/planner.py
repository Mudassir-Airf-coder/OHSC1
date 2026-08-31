"""Planner Agent.

Converts a natural-language user request into a structured, machine
 readable ``WorkflowPlan`` of ``Task`` objects. It maps intent keywords to
 agent actions, extracts structured parameters (title, content, query,
 tag, topic) from the request, identifies dependencies and marks the
 operation class (READ / WRITE / DESTRUCTIVE) and whether explicit
 authorization is needed.
"""

from __future__ import annotations

import re

from .contracts import OpClass, Task, TaskStatus, AgentResult
from .agent_base import BaseAgent, AgentContract
from .permissions import PermissionAgent
from .validation import validate_task

# Intent -> (agent, action, op_class) routing table. Extendable.
# Graph-intelligence rules are placed FIRST so that graph-specific phrasings
# ("find relationships", "find the shortest path", "find graph hubs") win over
# the generic search/find rule below. Linking/structural rules follow.
INTENT_RULES = [
    # -- most specific graph-intelligence phrasings FIRST (avoid greedy matches) --
    ("shortest path", "graphify_agent", "shortest_path", OpClass.READ),
    ("conceptual path", "graphify_agent", "shortest_path", OpClass.READ),
    ("multi-hop", "graphify_agent", "shortest_path", OpClass.READ),
    # Graph intelligence (Graphify) — semantic analysis, NOT wikilink editing.
    ("knowledge graph", "graphify_agent", "build", OpClass.READ),
    ("knowledge structure", "graphify_agent", "analyze", OpClass.READ),
    ("semantic", "graphify_agent", "query", OpClass.READ),
    ("conceptual path", "graphify_agent", "shortest_path", OpClass.READ),
    ("shortest path", "graphify_agent", "shortest_path", OpClass.READ),
    ("communities", "graphify_agent", "analyze", OpClass.READ),
    ("clusters", "graphify_agent", "analyze", OpClass.READ),
    ("concepts related", "graphify_agent", "query", OpClass.READ),
    ("hidden relationships", "graphify_agent", "query", OpClass.READ),
    ("explain how", "graphify_agent", "explain", OpClass.READ),
    ("local graph", "graphify_agent", "analyze", OpClass.READ),
    ("isolated concepts", "graphify_agent", "analyze", OpClass.READ),
    ("knowledge hubs", "graphify_agent", "analyze", OpClass.READ),
    ("graph hubs", "graphify_agent", "analyze", OpClass.READ),
    ("build a semantic graph", "graphify_agent", "build", OpClass.READ),
    ("analyze my vault", "graphify_agent", "build", OpClass.READ),
    ("graph connections", "graphify_agent", "analyze", OpClass.READ),
    ("graph report", "graphify_agent", "build", OpClass.READ),
    ("relationships between", "graphify_agent", "query", OpClass.READ),
    ("connections between", "graphify_agent", "query", OpClass.READ),
    ("connects", "graphify_agent", "query", OpClass.READ),
    ("central concepts", "graphify_agent", "analyze", OpClass.READ),
    ("most central", "graphify_agent", "analyze", OpClass.READ),
    ("central", "graphify_agent", "analyze", OpClass.READ),
    ("bridge", "graphify_agent", "analyze", OpClass.READ),
    ("multi-hop", "graphify_agent", "shortest_path", OpClass.READ),
    ("orphan", "linking_agent", "analyze", OpClass.READ),
    ("broken link", "linking_agent", "analyze", OpClass.READ),
    ("link", "linking_agent", "link", OpClass.WRITE),
    ("daily note", "periodic_agent", "create_daily", OpClass.WRITE),
    ("daily", "periodic_agent", "create_daily", OpClass.WRITE),
    ("weekly", "periodic_agent", "create_weekly", OpClass.WRITE),
    ("monthly", "periodic_agent", "create_monthly", OpClass.WRITE),
    ("moc", "dashboard_agent", "create_moc", OpClass.WRITE),
    ("dashboard", "dashboard_agent", "create_dashboard", OpClass.WRITE),
    ("index", "dashboard_agent", "create_index", OpClass.WRITE),
    ("template", "template_agent", "apply_template", OpClass.WRITE),
    ("metadata", "metadata_agent", "update_property", OpClass.WRITE),
    ("property", "metadata_agent", "update_property", OpClass.WRITE),
    ("tagged", "search_agent", "search_tag", OpClass.READ),
    ("tag", "search_agent", "search_tag", OpClass.READ),
    ("search", "search_agent", "search_text", OpClass.READ),
    ("find", "search_agent", "search_text", OpClass.READ),
    ("rename", "note_agent", "rename", OpClass.WRITE),
    ("move", "folder_agent", "move_note", OpClass.WRITE),
    ("folder", "folder_agent", "create_folder", OpClass.WRITE),
    ("delete", "note_agent", "delete", OpClass.DESTRUCTIVE),
    ("append", "note_agent", "append", OpClass.WRITE),
    ("update", "note_agent", "update", OpClass.WRITE),
    ("create note", "note_agent", "create", OpClass.WRITE),
    ("create", "note_agent", "create", OpClass.WRITE),
    ("read", "note_agent", "read", OpClass.READ),
    # Graph intelligence (Graphify) — semantic analysis, NOT wikilink editing.
    ("knowledge graph", "graphify_agent", "build", OpClass.READ),
    ("knowledge structure", "graphify_agent", "analyze", OpClass.READ),
    ("semantic", "graphify_agent", "query", OpClass.READ),
    ("conceptual path", "graphify_agent", "shortest_path", OpClass.READ),
    ("shortest path", "graphify_agent", "shortest_path", OpClass.READ),
    ("communities", "graphify_agent", "analyze", OpClass.READ),
    ("clusters", "graphify_agent", "analyze", OpClass.READ),
    ("concepts related", "graphify_agent", "query", OpClass.READ),
    ("hidden relationships", "graphify_agent", "query", OpClass.READ),
    ("explain how", "graphify_agent", "explain", OpClass.READ),
    ("local graph", "graphify_agent", "analyze", OpClass.READ),
    ("isolated concepts", "graphify_agent", "analyze", OpClass.READ),
    ("knowledge hubs", "graphify_agent", "analyze", OpClass.READ),
    ("build a semantic graph", "graphify_agent", "build", OpClass.READ),
    ("analyze my vault", "graphify_agent", "build", OpClass.READ),
]


def _extract_params(action: str, request: str) -> dict:
    """Pull structured parameters out of a natural-language request."""
    params: dict = {}
    rl = request.lower()
    if action in ("create", "update", "append"):
        # Prefer explicit "titled/named/called X"
        m = re.search(
            r"\b(?:titled|named|called|note titled|note named)\s+[\"']?([^\"'\n]+?)[\"']?"
            r"(?:\s+(?:with|and|containing)\s+|\s*$)",
            request, re.IGNORECASE)
        if not m:
            # "append to note X" / "update note X" / "create note X"
            m = re.search(
                r"\b(?:to|the|note)\s+note\s+[\"']?([^\"'\n]+?)[\"']?"
                r"(?:\s+(?:with|and|containing)\s+|\s*$)",
                request, re.IGNORECASE)
        if not m:
            m = re.search(
                r"\b(?:create|update|append)\s+(?:a\s+)?(?:note\s+)?[\"']?([^\"'\n]+?)[\"']?"
                r"(?:\s+(?:with|and|containing)\s+|\s*$)",
                request, re.IGNORECASE)
        if m:
            params["title"] = m.group(1).strip().strip("\"'")
        c = re.search(r"(?:with|and)\s+(?:content|text)\s+[\"']?([^\"']+)[\"']?", request, re.IGNORECASE)
        if c:
            params["content"] = c.group(1).strip()
    elif action in ("delete", "read", "rename"):
        m = re.search(
            r"(?:delete|read|rename)\s+(?:the\s+)?(?:note\s+)?[\"']?([^\"'\n]+?)[\"']?\s*$",
            request, re.IGNORECASE)
        if m:
            params["title"] = m.group(1).strip().strip("\"'")
        n = re.search(r"(?:to|as)\s+[\"']?([^\"'\n]+?)[\"']?\s*$", request, re.IGNORECASE)
        if action == "rename" and n:
            params["new_title"] = n.group(1).strip().strip("\"'")
    elif action in ("search_text",):
        q = re.sub(r"(?i)(search|find|for|notes?|containing|about)\s+", "", request).strip()
        params["query"] = q.strip("\"'")
        params["mode"] = "text"
    elif action == "search_tag":
        t = re.sub(r"(?i)(show|find|search|notes?|tagged|with tag|tag)\s+", "", request).strip()
        params["query"] = t.strip("#\"' ")
        params["mode"] = "tag"
    elif action in ("create_moc", "create_dashboard", "create_index"):
        t = re.sub(r"(?i)(create|make|a|moc|dashboard|index|for|about|on)\s+", "", request).strip()
        params["topic"] = t.strip("\"'")
    elif action in ("create_daily", "create_weekly", "create_monthly"):
        pass
    elif action in ("create_folder",):
        m = re.search(r"folder\s+[\"']?([^\"'\n]+?)[\"']?(?:\s|$)", request, re.IGNORECASE)
        if m:
            params["folder"] = m.group(1).strip().strip("\"'")
    elif action in ("shortest_path",):
        # "shortest path between A and B" / "path from A to B"
        m = re.search(r"(?:between|from)\s+[\"']?([^\"'\n]+?)[\"']?\s+(?:and|to)\s+[\"']?([^\"'\n]+?)[\"']?(?:\s*$|\s+in)", request, re.IGNORECASE)
        if m:
            params["source"] = m.group(1).strip().strip("\"'")
            params["target"] = m.group(2).strip().strip("\"'")
        else:
            # fallback: two capitalized-ish phrases
            m2 = re.search(r"shortest path\s+(?:between\s+)?([A-Za-z0-9 _-]+?)\s+(?:and|to)\s+([A-Za-z0-9 _-]+)", request, re.IGNORECASE)
            if m2:
                params["source"] = m2.group(1).strip()
                params["target"] = m2.group(2).strip()
    elif action in ("query", "analyze"):
        # strip routing keywords, keep the question
        q = re.sub(r"(?i)(find|show|analyze|generate|report|graph|knowledge|relationships|connections|hubs|communities|clusters|concepts|related|around|between these notes)\s+", " ", request)
        q = q.replace("the", "").replace("my vault", "").strip(" .")
        params["query"] = q.strip("\"'") or request
    elif action == "explain":
        # node = the subject being explained.
        # "explain how X connects to Y" / "explain X" -> X
        m = re.search(r"(?i)explain\s+(?:how\s+)?([A-Za-z0-9 _\-]+?)\s+(?:connects|relates|links|is|works|maps)\b", request)
        if not m:
            m = re.search(r"(?i)explain\s+(?:how\s+)?([A-Za-z0-9 _\-]+?)\s*$", request)
        node = m.group(1).strip().strip("\"'") if m else request
        params["node"] = node
    elif action in ("move_note",):
        s = re.search(r"move\s+(?:note\s+)?[\"']?([^\"'\n]+?)[\"']?\s+to\s+[\"']?([^\"'\n]+?)[\"']?", request, re.IGNORECASE)
        if s:
            params["title"] = s.group(1).strip().strip("\"'")
            params["dest"] = s.group(2).strip().strip("\"'")
        s = re.search(r"(?:link|connect)\s+([A-Za-z0-9 _-]+?)\s+(?:to|with|and)\s+([A-Za-z0-9 _-]+)", request, re.IGNORECASE)
        if s:
            params["source"] = s.group(1).strip()
            params["target"] = s.group(2).strip()
    return params


class PlannerAgent(BaseAgent):
    name = "planner_agent"
    role = "planner"
    contract = AgentContract(
        name=name, role=role,
        responsibilities=[
            "Parse natural-language requests",
            "Extract structured parameters",
            "Produce machine-readable execution plans",
            "Identify required agents and dependencies",
            "Classify operation risk (READ/WRITE/DESTRUCTIVE)",
        ],
        allowed_operations=["plan"],
        input_contract="natural language request + context",
        output_contract="WorkflowPlan (list of Tasks)",
        dependencies=["permission_agent"],
    )

    def __init__(self) -> None:
        super().__init__()
        self.perm = PermissionAgent()

    def plan(self, request: str, authorized: bool = False) -> "WorkflowPlanType":
        from .workflow_engine import WorkflowPlan

        request_l = request.lower()
        tasks: List[Task] = []
        used = set()
        for keyword, agent, action, op_class in INTENT_RULES:
            if keyword in request_l and agent not in used:
                authorized_for = authorized or op_class != OpClass.DESTRUCTIVE
                params = _extract_params(action, request)
                tasks.append(Task(
                    agent=agent, action=action, target="",
                    op_class=op_class, authorized=authorized_for,
                    params={"request": request, **params},
                ))
                used.add(agent)
                # A single clear intent is usually enough; stop after first
                # strong match unless the request is clearly compound.
                if keyword in ("create note", "delete", "daily note", "moc",
                               "search", "find", "tagged"):
                    break
        if not tasks:
            tasks.append(Task(
                agent="vault_agent", action="inspect",
                target="", op_class=OpClass.READ,
                params={"request": request},
            ))
        return WorkflowPlan(name=f"plan:{request[:40]}", tasks=tasks)

    def execute(self, task: Task) -> AgentResult:
        request = task.params.get("request", task.target)
        authorized = task.authorized
        plan = self.plan(request, authorized)

        def run(t: Task):
            return {"summary": f"Planned {len(plan.tasks)} step(s).",
                    "plan": plan.to_dict()}
        return self._wrap(task, run)


from .workflow_engine import WorkflowPlan as WorkflowPlanType  # noqa: E402
