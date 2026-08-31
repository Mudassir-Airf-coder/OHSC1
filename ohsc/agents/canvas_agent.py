"""Canvas Agent.

Creates, reads and safely modifies Obsidian Canvas (.canvas JSON) files.
Validates generated Canvas data and never corrupts existing canvas files.
"""

from __future__ import annotations

import json
from pathlib import Path

from ..core.agent_base import BaseAgent, AgentContract
from ..core.contracts import AgentResult, OpClass, Task, TaskStatus
from ..core.exceptions import ValidationError


class CanvasAgent(BaseAgent):
    name = "canvas_agent"
    role = "canvas"
    contract = AgentContract(
        name=name, role=role,
        responsibilities=[
            "Create/read/modify .canvas files", "Validate canvas JSON",
            "Never corrupt existing canvas files",
        ],
        allowed_operations=["create_canvas", "read_canvas", "add_node"],
        input_contract="canvas name + nodes",
        output_contract="canvas result",
        dependencies=["path_safety"],
    )

    def __init__(self, runtime) -> None:
        super().__init__()
        self.rt = runtime

    def _validate(self, data: dict) -> None:
        if not isinstance(data, dict):
            raise ValidationError("Canvas must be a JSON object.")
        if "nodes" not in data or "edges" not in data:
            raise ValidationError("Canvas requires 'nodes' and 'edges'.")
        if not isinstance(data["nodes"], list) or not isinstance(data["edges"], list):
            raise ValidationError("nodes/edges must be lists.")

    def execute(self, task: Task) -> AgentResult:
        rt = self.rt
        params = task.params
        action = task.action
        dry_run = params.get("dry_run", False)

        def run(t: Task):
            name = params.get("name", task.target)
            path = rt.safety.safe_join(rt.config.vault_root, f"{name}.canvas")
            if action == "create_canvas":
                data = {"nodes": [], "edges": []}
                self._validate(data)
                if dry_run:
                    return {"summary": f"[DRY-RUN] would create canvas {name}",
                            "would_create": str(path)}
                rt.backend.write_text(path, json.dumps(data, indent=2))
                return {"summary": f"Created canvas {name}", "path": str(path)}
            if action == "read_canvas":
                if not path.exists():
                    raise ValidationError(f"Canvas not found: {name}")
                data = json.loads(rt.backend.read_text(path))
                self._validate(data)
                return {"summary": f"Read canvas {name}",
                        "nodes": len(data["nodes"]), "edges": len(data["edges"])}
            if action == "add_node":
                if not path.exists():
                    raise ValidationError(f"Canvas not found: {name}")
                data = json.loads(rt.backend.read_text(path))
                self._validate(data)
                node = params.get("node", {"type": "text", "text": params.get("text", "")})
                node.setdefault("id", str(len(data["nodes"]) + 1))
                data["nodes"].append(node)
                if dry_run:
                    return {"summary": f"[DRY-RUN] would add node to {name}",
                            "would_modify": str(path)}
                rt.backend.write_text(path, json.dumps(data, indent=2))
                return {"summary": f"Added node to canvas {name}", "node_count": len(data["nodes"])}
            raise ValidationError(f"Unknown canvas action: {action}")
        return self._wrap(task, run)
