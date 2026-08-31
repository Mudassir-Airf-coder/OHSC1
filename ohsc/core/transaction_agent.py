"""Transaction / Rollback agent.

Implements the PREPARE -> SNAPSHOT -> EXECUTE -> VALIDATE -> COMMIT
pattern. On failure, attempts ROLLBACK where a snapshot exists. The
system never claims perfect rollback when the operation is not
mechanically reversible; it reports honestly.
"""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import Callable, Dict, List, Optional

from .snapshot_agent import SnapshotAgent, Snapshot
from .exceptions import TransactionError
from .agent_base import BaseAgent, AgentContract


@dataclass
class TransactionReport:
    label: str
    success: bool
    rolled_back: bool
    snapshot_id: Optional[str]
    steps: List[str] = field(default_factory=list)
    error: Optional[str] = None


class TransactionAgent(BaseAgent):
    """Runs operations under a prepare/snapshot/execute/validate/commit flow."""

    name = "transaction_agent"
    role = "transaction_rollback"
    contract = AgentContract(
        name=name, role=role,
        responsibilities=["Prepare/snapshot/execute/validate/commit", "Rollback on failure"],
        allowed_operations=["run"],
        input_contract="label + paths + execute + validate + reversible",
        output_contract="TransactionReport",
        dependencies=["snapshot_agent"],
    )

    def __init__(self, snapshot_agent: SnapshotAgent) -> None:
        super().__init__()
        self.snapshot_agent = snapshot_agent

    def run(
        self,
        label: str,
        affected_paths: List[str],
        execute: Callable[[], None],
        validate: Callable[[], bool],
        reversible: bool = True,
    ) -> TransactionReport:
        steps: List[str] = []
        snapshot: Optional[Snapshot] = None
        try:
            steps.append("PREPARE")
            if affected_paths:
                snapshot = self.snapshot_agent.capture(affected_paths, label=label)
                steps.append(f"SNAPSHOT({snapshot.id})")
            steps.append("EXECUTE")
            execute()
            steps.append("VALIDATE")
            if not validate():
                raise TransactionError("Post-execution validation failed.")
            steps.append("COMMIT")
            return TransactionReport(
                label=label, success=True, rolled_back=False,
                snapshot_id=snapshot.id if snapshot else None, steps=steps,
            )
        except Exception as exc:  # noqa: BLE001 - we must attempt rollback
            steps.append(f"FAILURE({type(exc).__name__})")
            if reversible and snapshot is not None:
                try:
                    self.snapshot_agent.restore(snapshot)
                    steps.append("ROLLBACK")
                    return TransactionReport(
                        label=label, success=False, rolled_back=True,
                        snapshot_id=snapshot.id, steps=steps, error=str(exc),
                    )
                except Exception as rb:  # noqa: BLE001
                    steps.append(f"ROLLBACK_FAILED({rb})")
                    return TransactionReport(
                        label=label, success=False, rolled_back=False,
                        snapshot_id=snapshot.id, steps=steps,
                        error=f"exec={exc}; rollback={rb}",
                    )
            return TransactionReport(
                label=label, success=False, rolled_back=False,
                snapshot_id=snapshot.id if snapshot else None,
                steps=steps, error=str(exc),
            )
