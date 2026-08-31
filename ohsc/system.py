"""Central bootstrap: register all agents into a Runtime's registry.

Adding a new agent only requires: define the agent class, then add one
line here. The core architecture stays stable.
"""

from __future__ import annotations

from .core.runtime import Runtime
from .agents.vault_agent import VaultAgent
from .agents.note_agent import NoteAgent
from .agents.search_agent import SearchAgent
from .agents.folder_agent import FolderAgent
from .agents.linking_agent import LinkingAgent
from .agents.metadata_agent import MetadataAgent
from .agents.template_agent import TemplateAgent
from .agents.periodic_agent import PeriodicAgent
from .agents.canvas_agent import CanvasAgent
from .agents.dashboard_agent import DashboardAgent
from .agents.bulk_agent import BulkAgent
from .agents.graphify_agent import GraphifyAgent
from .core.permissions import PermissionAgent
from .core.snapshot_agent import SnapshotAgent
from .core.transaction_agent import TransactionAgent
from .core.reviewer import ReviewerAgent


def build_runtime(config=None) -> Runtime:
    rt = Runtime(config)
    # Safety + infra agents
    rt.registry.register(PermissionAgent(), enabled=True)
    rt.registry.register(rt.snapshot_agent, enabled=True)
    rt.registry.register(rt.transaction_agent, enabled=True)
    rt.registry.register(ReviewerAgent(rt), enabled=True)
    # Specialized agents
    rt.registry.register(VaultAgent(rt), enabled=True)
    rt.registry.register(NoteAgent(rt), enabled=True)
    rt.registry.register(SearchAgent(rt), enabled=True)
    rt.registry.register(FolderAgent(rt), enabled=True)
    rt.registry.register(LinkingAgent(rt), enabled=True)
    rt.registry.register(MetadataAgent(rt), enabled=True)
    rt.registry.register(TemplateAgent(rt), enabled=True)
    rt.registry.register(PeriodicAgent(rt), enabled=True)
    rt.registry.register(CanvasAgent(rt), enabled=True)
    rt.registry.register(DashboardAgent(rt), enabled=True)
    rt.registry.register(BulkAgent(rt), enabled=True)
    # Graph intelligence layer (READ-ONLY on the vault; writes to OHSC workspace)
    rt.registry.register(GraphifyAgent(rt), enabled=True)
    return rt
