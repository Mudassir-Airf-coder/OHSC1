"""Agent base class and registry.

Every specialized agent inherits from ``BaseAgent`` and registers itself
so the Orchestrator can discover it, inspect its contract, check health
and dispatch tasks. The registry is the single source of truth for
"what agents exist".
"""

from __future__ import annotations

import time
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Dict, List, Optional

from .contracts import AgentResult, OpClass, Task
from .logging import get_logger, record_event


@dataclass
class AgentContract:
    name: str
    role: str
    responsibilities: List[str] = field(default_factory=list)
    allowed_operations: List[str] = field(default_factory=list)
    input_contract: str = ""
    output_contract: str = ""
    dependencies: List[str] = field(default_factory=list)
    permission_scope: str = ""
    reviewer_rules: List[str] = field(default_factory=list)


class BaseAgent(ABC):
    """Common agent scaffolding: identity, logging, execution wrapper."""

    name: str = "base_agent"
    role: str = "base"
    contract: AgentContract = None  # type: ignore

    def __init__(self) -> None:
        self.logger = get_logger(f"ohsc.agent.{self.name}")

    def _wrap(self, task: Task, fn) -> AgentResult:
        started = time.time()
        result = AgentResult(
            task_id=task.id, agent=self.name, status=__import__("ohsc.core.contracts", fromlist=["TaskStatus"]).TaskStatus.SUCCESS,
        )
        try:
            payload = fn(task)
            result.data = payload or {}
            result.summary = result.data.get("summary", f"{self.name} completed.")
        except Exception as exc:  # noqa: BLE001
            from .contracts import TaskStatus
            result.status = TaskStatus.FAILURE
            result.errors.append(f"{type(exc).__name__}: {exc}")
            result.summary = f"{self.name} failed: {exc}"
        finally:
            result.finished_at = time.time()
            result.duration_ms = (result.finished_at - started) * 1000
            record_event(
                task_id=task.id, agent=self.name, operation=task.action,
                target=task.target, result=result.status.value,
                duration_ms=result.duration_ms, errors=result.errors,
                warnings=result.warnings,
            )
        return result

    def execute(self, task: Task) -> AgentResult:
        """Run the agent for a task and return a structured result.

        Subclasses that are dispatched as workflow tasks must override this.
        Infrastructure agents (snapshot/permission/transaction) expose other
        methods and are not executed via the workflow engine.
        """
        raise NotImplementedError(f"{self.name} is not a workflow-executable agent.")

    def health(self) -> bool:
        return True


class AgentRegistry:
    """Single source of truth for all registered agents."""

    def __init__(self) -> None:
        self._agents: Dict[str, BaseAgent] = {}
        self._contracts: Dict[str, AgentContract] = {}
        self._enabled: Dict[str, bool] = {}

    def register(self, agent: BaseAgent, enabled: bool = True) -> None:
        self._agents[agent.name] = agent
        if agent.contract:
            self._contracts[agent.name] = agent.contract
        self._enabled[agent.name] = enabled

    def get(self, name: str) -> Optional[BaseAgent]:
        return self._agents.get(name)

    def dispatch(self, task: Task) -> AgentResult:
        agent = self._agents.get(task.agent)
        if agent is None:
            from .exceptions import AgentError
            raise AgentError(f"No such agent: {task.agent}")
        if not self._enabled.get(task.agent, False):
            from .contracts import TaskStatus
            return AgentResult(
                task_id=task.id, agent=task.agent,
                status=TaskStatus.FAILURE,
                summary=f"Agent {task.agent} is disabled.",
                errors=[f"Agent {task.agent} disabled"],
            )
        return agent.execute(task)

    # -- introspection ----------------------------------------------------
    def list_agents(self) -> List[Dict[str, object]]:
        out = []
        for name, agent in self._agents.items():
            c = self._contracts.get(name)
            out.append({
                "name": name,
                "role": c.role if c else agent.role,
                "enabled": self._enabled.get(name, False),
                "healthy": agent.health(),
                "responsibilities": c.responsibilities if c else [],
            })
        return out

    def summary(self) -> str:
        lines = [f"{'AGENT':<28} {'ROLE':<22} {'ENABLED':<8} HEALTHY"]
        for a in self.list_agents():
            lines.append(f"{a['name']:<28} {a['role']:<22} "
                         f"{str(a['enabled']):<8} {a['healthy']}")
        return "\n".join(lines)

    def count(self) -> int:
        return len(self._agents)

    def enabled_count(self) -> int:
        return sum(1 for v in self._enabled.values() if v)
