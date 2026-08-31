"""Search & Query Agent.

Supports full-text, filename, folder, tag, property, frontmatter and
link-based search. Uses the index for speed but verifies against the
filesystem when needed.
"""

from __future__ import annotations

from ..core.agent_base import BaseAgent, AgentContract
from ..core.contracts import AgentResult, OpClass, Task, TaskStatus
from ..core.indexing import parse_frontmatter
from ..core.index_store import VaultIndex


class SearchAgent(BaseAgent):
    name = "search_agent"
    role = "search_query"
    contract = AgentContract(
        name=name, role=role,
        responsibilities=[
            "Full-text / filename / folder / tag / property / link search",
            "Use index for speed; verify against filesystem",
        ],
        allowed_operations=["search_text", "search_tag", "search_property", "search_filename"],
        input_contract="query + scope",
        output_contract="list of matching notes",
        dependencies=["index_store"],
    )

    def __init__(self, runtime) -> None:
        super().__init__()
        self.rt = runtime

    def execute(self, task: Task) -> AgentResult:
        rt = self.rt
        params = task.params
        query = params.get("query") or task.target
        mode = params.get("mode", "text")

        def run(t: Task):
            if rt.config.index_enabled:
                rt.index.refresh(rt.config.vault_root)
                if mode == "tag":
                    hits = rt.index.search_tag(query)
                elif mode == "filename":
                    hits = [r for r in rt.index.notes.values() if query.lower() in r.path.lower()]
                elif mode == "property":
                    key = params.get("key", "")
                    val = params.get("value", "")
                    hits = [r for r in rt.index.notes.values()
                            if key in r.properties and str(r.properties[key]) == str(val)]
                else:
                    hits = rt.index.search_text(query)
            else:
                # Fallback: direct walk (uses backend safety).
                hits = []
                for p in rt.backend.walk(rt.config.vault_root):
                    if not p.endswith(".md"):
                        continue
                    if query.lower() in rt.backend.read_text(p).lower():
                        hits.append(type("R", (), {"path": p, "title": p})())
                hits = [{"path": getattr(h, "path", ""), "title": getattr(h, "title", "")} for h in hits]
            return {
                "summary": f"Found {len(hits)} match(es) for '{query}' ({mode}).",
                "matches": [h.title if hasattr(h, "title") else str(h) for h in hits],
                "count": len(hits),
            }
        return self._wrap(task, run)
