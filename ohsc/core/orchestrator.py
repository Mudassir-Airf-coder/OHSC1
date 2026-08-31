"""Orchestrator Agent.

The central controller. Receives a user request, asks the Planner for a
plan, runs it through the WorkflowEngine, triggers the Reviewer on the
result, and returns a user-friendly final result. It delegates all real
work to specialist agents and never implements operations itself.
"""

from __future__ import annotations

from .contracts import AgentResult, OpClass, Task, TaskStatus
from .planner import PlannerAgent
from .workflow_engine import WorkflowPlan, WorkflowReport
from .logging import get_logger


class Orchestrator:
    """Coordinates planner -> workflow -> reviewer -> result."""

    def __init__(self, runtime) -> None:
        self.rt = runtime
        self.planner = PlannerAgent()
        self.logger = get_logger("ohsc.orchestrator")

    def handle(
        self, request: str, authorized: bool = False, dry_run: bool = False,
        skip_review: bool = False,
    ) -> Dict[str, object]:
        # 1. Plan
        plan: WorkflowPlan = self.planner.plan(request, authorized)
        if dry_run:
            plan = self._apply_dry_run(plan)

        # 2. Execute via workflow engine
        report: WorkflowReport = self.rt.workflow.run(plan)

        # 3. Reviewer
        review = None
        if not skip_review:
            from .reviewer import ReviewerAgent
            reviewer = ReviewerAgent(self.rt)
            review = reviewer.review_workflow(report)

        # 4. Memory (remember successful request pattern)
        if report.passed:
            self.rt.memory.append("history", "requests",
                                  {"request": request, "ok": True})

        return {
            "request": request,
            "plan_steps": len(plan.tasks),
            "report": report.to_dict(),
            "review": review,
            "status": "SUCCESS" if report.passed else "FAILURE",
        }

    def _apply_dry_run(self, plan: WorkflowPlan) -> WorkflowPlan:
        # For dry-run we convert write/destructive tasks to a no-op inspect
        # and tag them so the agents report intended changes only.
        for t in plan.tasks:
            if t.op_class in (OpClass.WRITE, OpClass.DESTRUCTIVE):
                t.params = {**t.params, "dry_run": True}
        return plan
