"""Structured communication contracts between agents.

Agents communicate through typed ``Task`` and ``AgentResult`` objects
rather than uncontrolled free-form text. This gives us an auditable,
machine-readable protocol across the whole system.
"""

from __future__ import annotations

import time
import uuid
from dataclasses import dataclass, field, asdict
from enum import Enum
from typing import Any, Dict, List, Optional


class OpClass(str, Enum):
    """Classification of an operation's risk level."""

    READ = "READ"
    WRITE = "WRITE"
    DESTRUCTIVE = "DESTRUCTIVE"


class TaskStatus(str, Enum):
    PENDING = "PENDING"
    RUNNING = "RUNNING"
    SUCCESS = "SUCCESS"
    FAILURE = "FAILURE"
    SKIPPED = "SKIPPED"
    ROLLED_BACK = "ROLLED_BACK"


class Status(str, Enum):
    PASS = "PASS"
    PASS_WITH_WARNINGS = "PASS_WITH_WARNINGS"
    FAIL = "FAIL"


@dataclass
class Task:
    """A unit of work assigned to an agent."""

    id: str = field(default_factory=lambda: uuid.uuid4().hex[:12])
    agent: str = ""
    action: str = ""
    target: str = ""
    op_class: OpClass = OpClass.READ
    params: Dict[str, Any] = field(default_factory=dict)
    depends_on: List[str] = field(default_factory=list)
    authorized: bool = False
    created_at: float = field(default_factory=time.time)

    def to_dict(self) -> Dict[str, Any]:
        d = asdict(self)
        d["op_class"] = self.op_class.value
        return d

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Task":
        data = dict(data)
        data["op_class"] = OpClass(data.get("op_class", "READ"))
        return cls(**data)


@dataclass
class AgentResult:
    """The structured output an agent returns."""

    task_id: str = ""
    agent: str = ""
    status: TaskStatus = TaskStatus.SUCCESS
    summary: str = ""
    data: Dict[str, Any] = field(default_factory=dict)
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    started_at: float = field(default_factory=time.time)
    finished_at: float = field(default_factory=time.time)
    duration_ms: float = 0.0

    def to_dict(self) -> Dict[str, Any]:
        d = asdict(self)
        d["status"] = self.status.value
        return d

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "AgentResult":
        data = dict(data)
        data["status"] = TaskStatus(data.get("status", "SUCCESS"))
        return cls(**data)

    def ok(self) -> bool:
        return self.status in (TaskStatus.SUCCESS, TaskStatus.SKIPPED)
