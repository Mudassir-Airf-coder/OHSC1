"""Bulk Operations Agent.

Handles multi-file operations with preview, dry-run, transaction/snapshot
and rollback. Receives stronger safety checks than single-file ops and
reports partial failures.
"""

from __future__ import annotations

from ..core.agent_base import BaseAgent, AgentContract
from ..core.contracts import AgentResult, OpClass, Task, TaskStatus
from ..core.exceptions import PermissionError, ValidationError


class BulkAgent(BaseAgent):
    name = "bulk_agent"
    role = "bulk_operations"
    contract = AgentContract(
        name=name, role=role,
        responsibilities=[
            "Multi-file operations", "Preview affected files",
            "Dry-run", "Transaction + rollback", "Report partial failures",
        ],
        allowed_operations=["bulk_append", "bulk_tag", "bulk_move", "bulk_preview"],
        input_contract="selector + operation + params",
        output_contract="bulk result with per-file status",
        dependencies=["snapshot_agent", "transaction_agent", "index_store"],
    )

    def __init__(self, runtime) -> None:
        super().__init__()
        self.rt = runtime

    def _select(self, selector: dict):
        rt = self.rt
        rt.index.refresh(rt.config.vault_root)
        recs = list(rt.index.notes.values())
        if selector.get("tag"):
            recs = [r for r in recs if selector["tag"].lower() in [t.lower() for t in r.tags]]
        if selector.get("contains"):
            q = selector["contains"].lower()
            recs = [r for r in recs if q in r.title.lower()]
        return recs

    def execute(self, task: Task) -> AgentResult:
        rt = self.rt
        params = task.params
        action = task.action
        dry_run = params.get("dry_run", False)

        def run(t: Task):
            selector = params.get("selector", {})
            recs = self._select(selector)
            paths = [r.path for r in recs]

            if action == "bulk_preview" or dry_run:
                return {
                    "summary": f"[PREVIEW] {len(paths)} files would be affected by {action}.",
                    "affected": len(paths),
                    "files": [r.title for r in recs],
                    "dry_run": True,
                }

            # Non-preview bulk ops are WRITE/DESTRUCTIVE -> need authorization.
            if not task.authorized:
                raise PermissionError(f"Bulk op '{action}' requires authorization.")

            op = params.get("op", {})
            results = []
            for rec in recs:
                try:
                    text = rt.backend.read_text(rec.path)
                    new_text = text
                    if action == "bulk_append":
                        new_text = text + "\n" + op.get("content", "")
                    elif action == "bulk_tag":
                        tag = op.get("tag", "")
                        if f"#{tag}" not in text:
                            new_text = f"#{tag}\n" + text
                    elif action == "bulk_move":
                        dest = rt.safety.safe_join(rt.config.vault_root,
                                                   op.get("dest", ""), f"{rec.title}.md")
                        rt.backend.move(rec.path, dest)
                        results.append({"title": rec.title, "status": "moved"})
                        continue
                    rt.backend.write_text(rec.path, new_text)
                    results.append({"title": rec.title, "status": "ok"})
                except Exception as exc:  # noqa: BLE001 - report partial
                    results.append({"title": rec.title, "status": "error", "error": str(exc)})

            errors = [r for r in results if r["status"] == "error"]
            return {
                "summary": (f"Bulk {action}: {len(results)-len(errors)} ok, "
                            f"{len(errors)} failed of {len(recs)}."),
                "total": len(recs), "ok": len(results) - len(errors),
                "failed": len(errors), "details": results,
            }
        return self._wrap(task, run)
