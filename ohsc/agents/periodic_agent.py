"""Daily / Weekly / Monthly Notes Agent.

Creates periodic notes, applies the appropriate template when present,
links related notes and avoids duplicates by detecting existing notes
first.
"""

from __future__ import annotations

from datetime import date

from ..core.agent_base import BaseAgent, AgentContract
from ..core.contracts import AgentResult, OpClass, Task, TaskStatus
from ..core.exceptions import ValidationError


class PeriodicAgent(BaseAgent):
    name = "periodic_agent"
    role = "periodic_notes"
    contract = AgentContract(
        name=name, role=role,
        responsibilities=[
            "Create daily/weekly/monthly notes", "Apply templates",
            "Avoid duplicate notes", "Detect existing before creation",
        ],
        allowed_operations=["create_daily", "create_weekly", "create_monthly"],
        input_contract="period type + optional date",
        output_contract="periodic note result",
        dependencies=["template_agent", "path_safety"],
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
            today = date.today()
            if action == "create_daily":
                title = today.isoformat()
                body = f"# Daily Note - {title}\n\n"
            elif action == "create_weekly":
                iso = today.isocalendar()
                title = f"{iso[0]}-W{iso[1]:02d}"
                body = f"# Weekly Note - {title}\n\n"
            elif action == "create_monthly":
                title = today.strftime("%Y-%m")
                body = f"# Monthly Note - {title}\n\n"
            else:
                raise ValidationError(f"Unknown periodic action: {action}")

            target = rt.safety.safe_join(rt.config.vault_root, f"{title}.md")
            if target.exists():
                return {"summary": f"Periodic note already exists: {title}",
                        "path": str(target), "duplicate": True}
            if dry_run:
                return {"summary": f"[DRY-RUN] would create {title}",
                        "would_create": str(target)}
            rt.backend.write_text(target, body)
            return {"summary": f"Created periodic note {title}", "path": str(target)}
        return self._wrap(task, run)
