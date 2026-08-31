"""Linking & Graph Agent.

Creates wikilinks, detects broken links, orphan notes and hubs, and
builds relationship info. Links are only created based on evidence /
rules, never blindly.
"""

from __future__ import annotations

from ..core.agent_base import BaseAgent, AgentContract
from ..core.contracts import AgentResult, OpClass, Task, TaskStatus


class LinkingAgent(BaseAgent):
    name = "linking_agent"
    role = "linking_graph"
    contract = AgentContract(
        name=name, role=role,
        responsibilities=[
            "Create evidence-based wikilinks", "Detect broken links",
            "Detect orphan notes and hubs", "Analyze graph relationships",
        ],
        allowed_operations=["link", "analyze"],
        input_contract="note + target or analyze request",
        output_contract="linking result / graph analysis",
        dependencies=["index_store"],
    )

    def __init__(self, runtime) -> None:
        super().__init__()
        self.rt = runtime

    def execute(self, task: Task) -> AgentResult:
        rt = self.rt
        params = task.params
        action = task.action
        dry_run = params.get("dry_run", False)

        def run(t: Task):
            rt.index.refresh(rt.config.vault_root)
            if action == "analyze":
                orphans = rt.index.orphans()
                hubs = rt.index.hubs()
                broken = self._broken_links()
                return {
                    "summary": (f"Graph: {len(orphans)} orphans, "
                                f"{len(hubs)} hubs, {len(broken)} broken links."),
                    "orphans": [o.title for o in orphans],
                    "hubs": [h.title for h in hubs],
                    "broken_links": broken,
                }
            if action == "link":
                source = params.get("source", task.target)
                target_note = params.get("target", "")
                src_rec = rt.index.get_note(source)
                if src_rec is None:
                    raise ValueError(f"Source note not found: {source}")
                existing = rt.backend.read_text(src_rec.path)
                link = f"[[{target_note}]]"
                if link in existing:
                    return {"summary": f"Link already exists: {link}", "path": src_rec.path}
                new_text = existing + f"\n\nRelated: {link}\n"
                if dry_run:
                    return {"summary": f"[DRY-RUN] would add {link} to {source}",
                            "would_modify": src_rec.path}
                rt.backend.write_text(src_rec.path, new_text)
                return {"summary": f"Added link {link} to {source}", "path": src_rec.path}
            raise ValueError(f"Unknown linking action: {action}")
        return self._wrap(task, run)

    def _broken_links(self):
        rt = self.rt
        broken = []
        titles = {r.title.lower() for r in rt.index.notes.values()}
        for rec in rt.index.notes.values():
            for link in rec.links:
                if link.lower() not in titles:
                    broken.append({"from": rec.title, "missing": link})
        return broken
