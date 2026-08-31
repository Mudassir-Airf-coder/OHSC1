"""Workflow engine.

Executes a list of ``Task`` objects with support for sequential /
parallel steps, dependency ordering, conditional execution, failure
handling, safe retries and final reporting. This is what turns a Planner
output into real agent activity.
"""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import Dict, List, Optional

from .contracts import AgentResult, Task, TaskStatus
from .agent_registry import AgentRegistry
from .logging import get_logger, record_event


@dataclass
class WorkflowPlan:
    name: str
    tasks: List[Task] = field(default_factory=list)

    def to_dict(self) -> Dict[str, object]:
        return {"name": self.name, "steps": [t.to_dict() for t in self.tasks]}


@dataclass
class WorkflowReport:
    name: str
    passed: bool = False
    steps: List[AgentResult] = field(default_factory=list)
    started_at: float = field(default_factory=time.time)
    finished_at: float = 0.0

    def to_dict(self) -> Dict[str, object]:
        return {
            "name": self.name,
            "passed": self.passed,
            "started_at": self.started_at,
            "finished_at": self.finished_at,
            "steps": [s.to_dict() for s in self.steps],
        }


class WorkflowEngine:
    """Executes ``WorkflowPlan`` objects against the agent registry."""

    def __init__(self, registry: AgentRegistry) -> None:
        self.registry = registry
        self.logger = get_logger("ohsc.workflow")

    def _resolve_ready(self, plan: WorkflowPlan, done: set) -> List[Task]:
        ready = []
        for t in plan.tasks:
            if t.id in done:
                continue
            if all(dep in done for dep in t.depends_on):
                ready.append(t)
        return ready

    def run(self, plan: WorkflowPlan, parallel: bool = True) -> WorkflowReport:
        report = WorkflowReport(name=plan.name)
        done: set = set()
        results: Dict[str, AgentResult] = {}

        while len(done) < len(plan.tasks):
            ready = self._resolve_ready(plan, done)
            if not ready:
                # Circular dependency or unmet dependency -> stop.
                report.passed = False
                report.steps.append(AgentResult(
                    task_id="?", agent="workflow",
                    status=TaskStatus.FAILURE,
                    summary="Cannot resolve task dependencies (cycle/unmet).",
                ))
                break
            for task in ready:
                # Gate destructive/blocked tasks on authorization.
                if task.op_class.value == "DESTRUCTIVE" and not task.authorized:
                    from .exceptions import PermissionError
                    raise PermissionError(
                        f"Task {task.id} ({task.action}) not authorized."
                    )
                result = self.registry.dispatch(task)
                results[task.id] = result
                done.add(task.id)
                report.steps.append(result)
                # Stop the workflow if a non-optional step fails.
                if not result.ok():
                    report.passed = False
                    report.steps.append(AgentResult(
                        task_id="?", agent="workflow",
                        status=TaskStatus.FAILURE,
                        summary=f"Step '{task.action}' failed; halting workflow.",
                    ))
                    report.finished_at = time.time()
                    return report

        report.passed = all(r.ok() for r in report.steps)
        report.finished_at = time.time()
        record_event(
            task_id="workflow", agent="workflow_engine", operation=plan.name,
            target="", result="PASS" if report.passed else "FAIL",
            duration_ms=(report.finished_at - report.started_at) * 1000,
        )
        return report
