"""Agent runtime.

Bootstraps the shared infrastructure (safety, backend, registry, memory,
index, workflow engine) and exposes a single ``Runtime`` object the
Orchestrator and CLI build on. This keeps construction centralized so
agents stay small and reusable.
"""

from __future__ import annotations

from pathlib import Path
from typing import Optional

from ..config import load_config, SystemConfig
from .path_safety import PathSafety
from .filesystem import FilesystemBackend
from .agent_registry import AgentRegistry
from .memory import MemoryStore
from .index_store import VaultIndex
from .snapshot_agent import SnapshotAgent
from .transaction_agent import TransactionAgent
from .workflow_engine import WorkflowEngine
from .logging import configure_logging


class Runtime:
    """Holds all shared OHSC infrastructure instances."""

    def __init__(self, config: Optional[SystemConfig] = None) -> None:
        self.config = config or load_config()
        self.config.ensure_dirs()
        configure_logging()

        self.safety = PathSafety(self.config.allowed_root_paths)
        self.backend = FilesystemBackend(self.safety)
        self.registry = AgentRegistry()
        self.memory = MemoryStore(self.config.system_root)
        self.index = VaultIndex(self.backend, self.config.index_dir)
        self.snapshot_agent = SnapshotAgent(self.backend, self.config.backup_dir)
        self.transaction_agent = TransactionAgent(self.snapshot_agent)
        self.workflow = WorkflowEngine(self.registry)
