"""Canonical agent base imports.

``BaseAgent`` and ``AgentContract`` are defined in ``agent_registry`` but
imported here so all agents can do ``from .agent_base import BaseAgent``.
"""

from .agent_registry import BaseAgent, AgentContract

__all__ = ["BaseAgent", "AgentContract"]
