"""Graphify integration configuration.

All Graphify system data lives under the OHSC workspace, OUTSIDE the real
Obsidian vault. This module is the single source of truth for those paths.
"""

from __future__ import annotations

from pathlib import Path
from typing import Dict, Any


def default_workspace(system_root: Path) -> Dict[str, Path]:
    base = Path(system_root) / "graphify"
    paths = {
        "root": base,
        "graphs": base / "graphs",
        "reports": base / "reports",
        "cache": base / "cache",
        "exports": base / "exports",
        "logs": base / "logs",
        "config": base / "config",
    }
    return paths


def ensure_workspace(system_root: Path) -> Dict[str, Path]:
    paths = default_workspace(system_root)
    for p in paths.values():
        p.mkdir(parents=True, exist_ok=True)
    return paths


def to_dict(system_root: Path) -> Dict[str, Any]:
    return {k: str(v) for k, v in default_workspace(system_root).items()}
