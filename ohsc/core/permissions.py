"""Permission / Intent classification.

Every operation is classified as READ, WRITE or DESTRUCTIVE. Destructive
operations require explicit user authorization before they may run.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List

from .contracts import OpClass
from .agent_base import BaseAgent, AgentContract


# Operations -> classification map. Extend as new operations are added.
_OPERATION_MAP: Dict[str, OpClass] = {
    # Read
    "search": OpClass.READ,
    "read": OpClass.READ,
    "list": OpClass.READ,
    "analyze": OpClass.READ,
    "inspect": OpClass.READ,
    "index": OpClass.READ,
    "validate": OpClass.READ,
    # Write
    "create": OpClass.WRITE,
    "append": OpClass.WRITE,
    "update": OpClass.WRITE,
    "move": OpClass.WRITE,
    "rename": OpClass.WRITE,
    "apply_template": OpClass.WRITE,
    "set_property": OpClass.WRITE,
    "link": OpClass.WRITE,
    # Destructive
    "delete": OpClass.DESTRUCTIVE,
    "mass_delete": OpClass.DESTRUCTIVE,
    "mass_replace": OpClass.DESTRUCTIVE,
    "purge": OpClass.DESTRUCTIVE,
}


@dataclass
class PermissionDecision:
    operation: str
    op_class: OpClass
    authorized: bool
    reason: str = ""


class PermissionAgent(BaseAgent):
    """Classifies intent and enforces authorization rules."""

    name = "permission_agent"
    role = "permission_intent"
    contract = AgentContract(
        name=name, role=role,
        responsibilities=["Classify READ/WRITE/DESTRUCTIVE", "Enforce auth rules"],
        allowed_operations=["classify", "decide", "require"],
        input_contract="operation name",
        output_contract="PermissionDecision",
        dependencies=[],
    )

    def classify(self, operation: str) -> OpClass:
        op = (operation or "").lower()
        if op in _OPERATION_MAP:
            return _OPERATION_MAP[op]
        # Heuristic fallback for unknown operations.
        if any(k in op for k in ("del", "remove", "purge", "wipe", "erase")):
            return OpClass.DESTRUCTIVE
        if any(k in op for k in ("cre", "add", "append", "update", "mov", "renam", "write", "set")):
            return OpClass.WRITE
        return OpClass.READ

    def decide(
        self, operation: str, user_authorized: bool = False
    ) -> PermissionDecision:
        op_class = self.classify(operation)
        if op_class == OpClass.READ:
            authorized = True
            reason = "Read operations are safe and implicitly authorized."
        elif op_class == OpClass.WRITE:
            authorized = True
            reason = "Write operations are authorized by an explicit user request."
        else:  # DESTRUCTIVE
            authorized = bool(user_authorized)
            reason = (
                "Destructive operation authorized by user."
                if user_authorized
                else "Destructive operation requires explicit user authorization."
            )
        return PermissionDecision(operation=operation, op_class=op_class,
                                   authorized=authorized, reason=reason)

    def require(self, operation: str, user_authorized: bool = False) -> None:
        from .exceptions import PermissionError

        decision = self.decide(operation, user_authorized)
        if not decision.authorized:
            raise PermissionError(
                f"Operation '{operation}' blocked: {decision.reason}"
            )
