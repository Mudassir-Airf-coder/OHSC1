"""Dashboard / MOC Agent.

Creates Maps of Content, indexes and dashboards by connecting related
notes. Preserves existing content unless explicitly instructed otherwise.
"""

from __future__ import annotations

from ..core.agent_base import BaseAgent, AgentContract
from ..core.contracts import AgentResult, OpClass, Task, TaskStatus
from ..core.filesystem import VaultBackend


class DashboardAgent(BaseAgent):
    name = "dashboard_agent"
    role = "dashboard_moc"
    contract = AgentContract(
        name=name, role=role,
        responsibilities=[
            "Create MOCs, indexes, dashboards", "Connect related notes",
            "Preserve existing content unless told otherwise",
        ],
        allowed_operations=["create_moc", "create_index", "create_dashboard"],
        input_contract="topic + scope",
        output_contract="dashboard/moc result",
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
            topic = params.get("topic", task.target) or "Index"
            if action in ("create_moc", "create_index", "create_dashboard"):
                # Collect related notes by topic keyword in title or tags.
                kw = topic.lower()
                related = [r for r in rt.index.notes.values()
                           if kw in r.title.lower()
                           or any(kw in tg.lower() for tg in r.tags)]
                lines = [f"# MOC: {topic}", "", "## Related Notes", ""]
                for r in sorted(related, key=lambda x: x.title):
                    lines.append(f"- [[{r.title}]]")
                if not related:
                    lines.append("- (no related notes found)")
                content = "\n".join(lines) + "\n"
                fname = f"MOC - {topic}" if action == "create_moc" else f"Index - {topic}"
                path = rt.safety.safe_join(rt.config.vault_root, f"{fname}.md")
                if dry_run:
                    return {"summary": f"[DRY-RUN] would create {fname}",
                            "would_create": str(path), "links": len(related)}
                rt.backend.write_text(path, content)
                return {"summary": f"Created {fname} with {len(related)} links",
                        "path": str(path), "links": len(related)}
            raise ValueError(f"Unknown dashboard action: {action}")
        return self._wrap(task, run)
