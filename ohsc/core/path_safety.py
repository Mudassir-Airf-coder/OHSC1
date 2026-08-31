"""Centralized path safety.

Every filesystem operation in OHSC MUST pass through the ``PathSafety``
guard. No agent may touch a path outside the approved roots
(``D:\\HOSC`` and ``D:\\Mudassir database``). Path traversal, unexpected
absolute paths and unauthorized directories are blocked here.
"""

from __future__ import annotations

from pathlib import Path
from typing import List, Union

from .exceptions import PathSafetyError


class PathSafety:
    """Validates that a target path lives inside an allowed root."""

    def __init__(self, allowed_roots: List[Union[str, Path]]) -> None:
        self.allowed_roots = [Path(p).resolve() for p in allowed_roots]

    @classmethod
    def from_config(cls) -> "PathSafety":
        from ..config import load_config

        cfg = load_config()
        return cls(cfg.allowed_root_paths)

    def is_allowed(self, path: Union[str, Path]) -> bool:
        try:
            resolved = Path(path).resolve()
        except Exception:
            return False
        for root in self.allowed_roots:
            try:
                resolved.relative_to(root)
                return True
            except ValueError:
                continue
        return False

    def validate(self, path: Union[str, Path]) -> Path:
        """Return the resolved, allowed path or raise ``PathSafetyError``."""
        try:
            resolved = Path(path).resolve()
        except Exception as exc:  # pragma: no cover - OS edge cases
            raise PathSafetyError(f"Cannot resolve path '{path}': {exc}")

        # Reject obvious traversal components explicitly for clear messaging.
        raw = str(path)
        if ".." in Path(raw).parts:
            raise PathSafetyError(
                f"Path traversal ('..') is not allowed: {path}"
            )

        if not self.is_allowed(resolved):
            raise PathSafetyError(
                f"Path '{resolved}' is outside the allowed roots: "
                f"{[str(r) for r in self.allowed_roots]}"
            )
        return resolved

    def safe_join(self, base: Union[str, Path], *parts: str) -> Path:
        """Safely join parts under a base that must itself be allowed."""
        base_path = self.validate(base)
        candidate = base_path.joinpath(*parts)
        return self.validate(candidate)

    def allowed_roots_list(self) -> List[str]:
        return [str(r) for r in self.allowed_roots]
