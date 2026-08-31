"""Template Agent.

Discovers templates (files in a _templates folder or marked with a
template tag), validates them, and applies them to new notes. Supports
reusable workflows.
"""

from __future__ import annotations

from pathlib import Path

from ..core.agent_base import BaseAgent, AgentContract
from ..core.contracts import AgentResult, OpClass, Task, TaskStatus
from ..core.exceptions import ValidationError


class TemplateAgent(BaseAgent):
    name = "template_agent"
    role = "template"
    contract = AgentContract(
        name=name, role=role,
        responsibilities=[
            "Discover/validate/create templates", "Apply templates to notes",
        ],
        allowed_operations=["apply_template", "list_templates", "create_template"],
        input_contract="template name + target note",
        output_contract="applied template result",
        dependencies=["path_safety"],
    )

    def __init__(self, runtime) -> None:
        super().__init__()
        self.rt = runtime

    def _templates_dir(self) -> Path:
        return self.rt.safety.safe_join(self.rt.config.vault_root, "_templates")

    def execute(self, task: Task) -> AgentResult:
        rt = self.rt
        params = task.params
        action = task.action
        dry_run = params.get("dry_run", False)

        def run(t: Task):
            tdir = self._templates_dir()
            if action == "list_templates":
                if not tdir.exists():
                    return {"summary": "No templates folder.", "templates": []}
                tmpls = [p.stem for p in tdir.glob("*.md")]
                return {"summary": f"{len(tmpls)} templates.", "templates": tmpls}
            if action == "create_template":
                name = params.get("name", task.target)
                content = params.get("content", "")
                rt.backend.mkdir(tdir)
                rt.backend.write_text(tdir / f"{name}.md", content)
                return {"summary": f"Created template {name}", "path": str(tdir / name)}
            if action == "apply_template":
                name = params.get("name", task.target)
                target_title = params.get("title", "")
                tpl_path = tdir / f"{name}.md"
                if not tpl_path.exists():
                    raise ValidationError(f"Template not found: {name}")
                content = rt.backend.read_text(tpl_path)
                dest = rt.safety.safe_join(rt.config.vault_root, f"{target_title}.md")
                if dry_run:
                    return {"summary": f"[DRY-RUN] would apply '{name}' to {target_title}",
                            "would_create": str(dest)}
                rt.backend.write_text(dest, content)
                return {"summary": f"Applied template '{name}' to {target_title}",
                        "path": str(dest)}
            raise ValidationError(f"Unknown template action: {action}")
        return self._wrap(task, run)
