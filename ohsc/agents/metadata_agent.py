"""Properties & Metadata Agent.

Reads/creates/updates frontmatter, normalizes metadata, manages tags and
validates property formats. Never overwrites unrelated metadata.
"""

from __future__ import annotations

from ..core.agent_base import BaseAgent, AgentContract
from ..core.contracts import AgentResult, OpClass, Task, TaskStatus
from ..core.indexing import parse_frontmatter, FRONTMATTER_RE
from ..core.exceptions import ValidationError


class MetadataAgent(BaseAgent):
    name = "metadata_agent"
    role = "properties_metadata"
    contract = AgentContract(
        name=name, role=role,
        responsibilities=[
            "Read/create/update frontmatter", "Normalize metadata",
            "Manage tags", "Validate property formats",
            "Preserve unrelated existing metadata",
        ],
        allowed_operations=["read_property", "update_property", "normalize"],
        input_contract="note + property dict",
        output_contract="metadata result",
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
            title = params.get("title", task.target)
            rec = rt.index.get_note(title)
            if rec is None:
                # allow creating metadata on a fresh note
                path = rt.safety.safe_join(rt.config.vault_root, f"{title}.md")
                if not path.exists():
                    raise ValidationError(f"Note not found: {title}")
            else:
                path = rt.safety.validate(rec.path)
            text = rt.backend.read_text(path)
            props, body = parse_frontmatter(text)

            if action == "update_property":
                updates = params.get("properties", {})
                for k, v in updates.items():
                    props[k] = v
                new_text = self._serialize(props, body)
                if dry_run:
                    return {"summary": f"[DRY-RUN] would update metadata of {title}",
                            "would_modify": str(path)}
                rt.backend.write_text(path, new_text)
                return {"summary": f"Updated metadata for {title}", "properties": props,
                        "preserved_others": True}
            if action == "read_property":
                return {"summary": f"Read metadata for {title}", "properties": props}
            if action == "normalize":
                # lowercase tags, ensure tags is a list
                if "tags" in props:
                    tg = props["tags"]
                    tg = [tg] if isinstance(tg, str) else list(tg)
                    props["tags"] = sorted({str(x).lower().lstrip("#") for x in tg})
                new_text = self._serialize(props, body)
                if dry_run:
                    return {"summary": f"[DRY-RUN] would normalize {title}",
                            "would_modify": str(path)}
                rt.backend.write_text(path, new_text)
                return {"summary": f"Normalized metadata for {title}", "properties": props}
            raise ValidationError(f"Unknown metadata action: {action}")
        return self._wrap(task, run)

    @staticmethod
    def _serialize(props, body: str) -> str:
        if not props:
            return body.lstrip("\n")
        lines = ["---"]
        for k, v in props.items():
            if isinstance(v, list):
                lines.append(f"{k}:")
                for item in v:
                    lines.append(f"  - {item}")
            elif isinstance(v, bool):
                lines.append(f"{k}: {'true' if v else 'false'}")
            else:
                lines.append(f"{k}: {v}")
        lines.append("---")
        return "\n".join(lines) + "\n" + body
