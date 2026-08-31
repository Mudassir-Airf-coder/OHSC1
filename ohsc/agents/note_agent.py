"""Note CRUD Agent.

Separate responsibilities for create / read / update / append / rename /
delete. Read is always safe; write requires the request's authorization;
delete is destructive and requires explicit authorization. Never silently
deletes notes.
"""

from __future__ import annotations

from pathlib import Path

from ..core.agent_base import BaseAgent, AgentContract
from ..core.contracts import AgentResult, OpClass, Task, TaskStatus
from ..core.exceptions import PermissionError, ValidationError
from ..core.validation import validate_note_name


class NoteAgent(BaseAgent):
    name = "note_agent"
    role = "note_crud"
    contract = AgentContract(
        name=name, role=role,
        responsibilities=[
            "Create, Read, Update, Append, Rename, Delete notes",
            "Enforce authorization for write/destructive ops",
            "Never silently delete notes",
        ],
        allowed_operations=["create", "read", "update", "append", "rename", "delete"],
        input_contract="action + title + content/folder",
        output_contract="note result dict",
        dependencies=["path_safety", "permission_agent"],
    )

    def __init__(self, runtime) -> None:
        super().__init__()
        self.rt = runtime

    def _path_for(self, title: str, folder: str = "") -> Path:
        base = self.rt.config.vault_root
        if folder:
            return self.rt.safety.safe_join(base, folder, f"{title}.md")
        return self.rt.safety.safe_join(base, f"{title}.md")

    def execute(self, task: Task) -> AgentResult:
        rt = self.rt
        action = task.action
        params = task.params
        folder = params.get("folder", "")
        content = params.get("content", "")
        dry_run = params.get("dry_run", False)

        def run(t: Task):
            title = validate_note_name(params.get("title") or params.get("name") or task.target)
            target = self._path_for(title, folder)
            if action == "read":
                return {"summary": f"Read {target.name}",
                        "content": rt.backend.read_text(target)}
            if action == "create":
                if target.exists():
                    raise ValidationError(f"Note already exists: {target.name}")
                if dry_run:
                    return {"summary": f"[DRY-RUN] would create {target}",
                            "would_create": str(target)}
                rt.backend.write_text(target, content)
                return {"summary": f"Created {target.name}", "path": str(target)}
            if action == "update":
                if dry_run:
                    return {"summary": f"[DRY-RUN] would overwrite {target}",
                            "would_modify": str(target)}
                rt.backend.write_text(target, content)
                return {"summary": f"Updated {target.name}", "path": str(target)}
            if action == "append":
                existing = rt.backend.read_text(target) if target.exists() else ""
                new = existing + "\n" + content if existing else content
                if dry_run:
                    return {"summary": f"[DRY-RUN] would append to {target}",
                            "would_modify": str(target)}
                rt.backend.write_text(target, new)
                return {"summary": f"Appended to {target.name}", "path": str(target)}
            if action == "rename":
                new_title = validate_note_name(params.get("new_title", ""))
                new_target = self._path_for(new_title, folder)
                if dry_run:
                    return {"summary": f"[DRY-RUN] would rename {target} -> {new_target}",
                            "would_move": str(target), "to": str(new_target)}
                rt.backend.move(target, new_target)
                return {"summary": f"Renamed to {new_target.name}",
                        "path": str(new_target)}
            if action == "delete":
                if not task.authorized:
                    raise PermissionError("Delete requires explicit authorization.")
                if not target.exists():
                    raise ValidationError(f"Note not found: {target.name}")
                if dry_run:
                    return {"summary": f"[DRY-RUN] would delete {target}",
                            "would_delete": str(target)}
                rt.backend.remove(target)
                return {"summary": f"Deleted {target.name}", "path": str(target)}
            raise ValidationError(f"Unknown note action: {action}")

        return self._wrap(task, run)
