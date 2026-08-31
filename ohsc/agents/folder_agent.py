"""Folder Structure Agent.

Creates folders, renames folders, moves notes, analyzes organization and
suggests improvements. Performs changes only when authorized.
"""

from __future__ import annotations

from pathlib import Path

from ..core.agent_base import BaseAgent, AgentContract
from ..core.contracts import AgentResult, OpClass, Task, TaskStatus
from ..core.exceptions import ValidationError


class FolderAgent(BaseAgent):
    name = "folder_agent"
    role = "folder_structure"
    contract = AgentContract(
        name=name, role=role,
        responsibilities=[
            "Create/rename folders", "Move notes", "Analyze organization",
            "Suggest improvements",
        ],
        allowed_operations=["create_folder", "rename_folder", "move_note", "analyze"],
        input_contract="folder path / note + destination",
        output_contract="folder operation result",
        dependencies=["path_safety"],
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
            if action == "create_folder":
                folder = params.get("folder", task.target)
                if not folder:
                    raise ValidationError("folder required")
                target = rt.safety.safe_join(rt.config.vault_root, folder)
                if dry_run:
                    return {"summary": f"[DRY-RUN] would create {target}", "would_create": str(target)}
                rt.backend.mkdir(target)
                return {"summary": f"Created folder {target}", "path": str(target)}
            if action == "move_note":
                src_title = params.get("title", task.target)
                dest_folder = params.get("dest", "")
                src = rt.safety.safe_join(rt.config.vault_root, f"{src_title}.md")
                dst = rt.safety.safe_join(rt.config.vault_root, dest_folder, f"{src_title}.md")
                if dry_run:
                    return {"summary": f"[DRY-RUN] would move {src} -> {dst}",
                            "would_move": str(src), "to": str(dst)}
                rt.backend.move(src, dst)
                return {"summary": f"Moved {src_title} -> {dest_folder}", "path": str(dst)}
            if action == "analyze":
                folders = set()
                for p in rt.backend.walk(rt.config.vault_root):
                    if ".obsidian" in p:
                        continue
                    fp = Path(p)
                    if fp.is_dir():
                        folders.add(str(fp.relative_to(rt.config.vault_root)))
                return {"summary": f"Found {len(folders)} folders.",
                        "folders": sorted(folders)}
            raise ValidationError(f"Unknown folder action: {action}")
        return self._wrap(task, run)
