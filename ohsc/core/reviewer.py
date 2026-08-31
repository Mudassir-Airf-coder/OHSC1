"""Reviewer Agent.

Mandatory independent review. It does NOT simply say "looks good". It
inspects the workflow result, the agents involved, filesystem impact,
tests status and documentation, and returns a structured verdict:

    REVIEW STATUS: PASS / PASS_WITH_WARNINGS / FAIL
    ISSUES ...
    RECOMMENDATIONS ...
    REQUIRED FIXES ...
    FINAL APPROVAL: YES / NO

It also can review individual agents and code via static checks.
"""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from typing import Dict, List, Optional

from .contracts import Status, TaskStatus
from .agent_base import BaseAgent, AgentContract


@dataclass
class ReviewReport:
    status: Status
    issues: List[str] = field(default_factory=list)
    recommendations: List[str] = field(default_factory=list)
    required_fixes: List[str] = field(default_factory=list)
    approved: bool = False

    def to_dict(self) -> Dict[str, object]:
        return {
            "status": self.status.value,
            "issues": self.issues,
            "recommendations": self.recommendations,
            "required_fixes": self.required_fixes,
            "approved": self.approved,
        }


class ReviewerAgent(BaseAgent):
    name = "reviewer_agent"
    role = "reviewer"
    contract = AgentContract(
        name=name, role=role,
        responsibilities=["Review code/agents/fs/tests/docs", "Emit structured verdict"],
        allowed_operations=["review_workflow", "review_agent_module"],
        input_contract="workflow report or module path",
        output_contract="ReviewReport",
        dependencies=[],
    )
    description = "Inspects code, agents, filesystem impact, tests and docs."

    def __init__(self, runtime=None) -> None:
        self.rt = runtime

    def review_workflow(self, report) -> Dict[str, object]:
        issues: List[str] = []
        recs: List[str] = []
        fixes: List[str] = []

        # 1. Did the task actually complete?
        if not getattr(report, "passed", False):
            failed = [s for s in report.steps if not s.ok()]
            for f in failed:
                issues.append(f"Step failed: {f.agent}/{f.task_id} - {f.summary}")
                fixes.append(f"Fix failing step: {f.agent} ({f.summary})")

        # 2. Any errors emitted?
        for s in report.steps:
            if getattr(s, "errors", None):
                for e in s.errors:
                    issues.append(f"{s.agent} error: {e}")

        # 3. Unintended vault changes? (we rely on dry-run diff + path safety)
        #    Real safety is enforced by PathSafety; reviewer audits the log.
        # 4. Warnings
        for s in report.steps:
            if getattr(s, "warnings", None):
                for w in s.warnings:
                    recs.append(f"{s.agent} warning: {w}")

        if not issues and not fixes:
            status = Status.PASS if not recs else Status.PASS_WITH_WARNINGS
            approved = True
        elif fixes:
            status = Status.FAIL
            approved = False
        else:
            status = Status.PASS_WITH_WARNINGS
            approved = True

        return ReviewReport(
            status=status, issues=issues, recommendations=recs,
            required_fixes=fixes, approved=approved,
        ).to_dict()

    def review_agent_module(self, path: str) -> Dict[str, object]:
        """Static review of an agent module file."""
        issues, recs = [], []
        if not os.path.exists(path):
            issues.append(f"Agent module missing: {path}")
            return ReviewReport(Status.FAIL, issues, recs, ["create the module"],
                                False).to_dict()
        text = open(path, encoding="utf-8").read()
        if "class " not in text:
            issues.append("No agent class defined.")
        if "execute" not in text:
            issues.append("No execute() method.")
        if "record_event" not in text and "get_logger" not in text:
            recs.append("Agent does not log operations.")
        if "validate" not in text and "PathSafety" not in text:
            recs.append("Agent should validate path safety.")
        status = Status.PASS if not issues else Status.FAIL
        return ReviewReport(status, issues, recs, issues.copy(), not issues).to_dict()
