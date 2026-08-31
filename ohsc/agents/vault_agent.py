"""Vault Management Agent.

Verifies the vault path, inspects structure and validates availability.
Never assumes the vault exists; never silently switches to another vault.
"""

from __future__ import annotations

from ..core.agent_base import BaseAgent, AgentContract
from ..core.contracts import AgentResult, OpClass, Task, TaskStatus
from ..core.exceptions import ValidationError


class VaultAgent(BaseAgent):
    name = "vault_agent"
    role = "vault_management"
    contract = AgentContract(
        name=name, role=role,
        responsibilities=[
            "Verify vault path",
            "Inspect vault structure",
            "Validate vault availability",
            "Never assume the vault exists",
        ],
        allowed_operations=["inspect", "validate"],
        input_contract="vault root path",
        output_contract="vault status dict",
        dependencies=[],
    )

    def __init__(self, runtime) -> None:
        super().__init__()
        self.rt = runtime

    def execute(self, task: Task) -> AgentResult:
        rt = self.rt

        def run(t: Task):
            vault_path = rt.config.vault_root
            exists = rt.safety.is_allowed(vault_path) and vault_path.exists()
            md_files = []
            if exists:
                try:
                    md_files = [p for p in vault_path.rglob("*.md")]
                except Exception:
                    md_files = []
            if not exists:
                raise ValidationError(f"Vault not found at {vault_path}")
            return {
                "summary": f"Vault OK: {len(md_files)} markdown files.",
                "vault_root": str(vault_path),
                "exists": True,
                "markdown_count": len(md_files),
            }
        return self._wrap(task, run)
