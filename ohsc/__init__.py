"""OHSC — Obsidian System Control.

A modular, autonomous, multi-agent control plane for managing an Obsidian
vault safely from the CLI or any external AI coding agent.
"""

from .system import build_runtime
from .config import load_config, SystemConfig

__version__ = "1.0.0"
__system_name__ = "Obsidian System Control"

__all__ = ["build_runtime", "load_config", "SystemConfig", "__version__"]
