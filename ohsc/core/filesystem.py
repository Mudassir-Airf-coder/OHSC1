"""Filesystem abstraction layer.

The ``VaultBackend`` abstract interface lets OHSC interact with a vault
without being coupled to a concrete mechanism. ``FilesystemBackend`` is
the first-class implementation (Markdown files on disk). A future
``ObsidianRestBackend`` could implement the same interface without
changing any agent. ALL operations still pass through ``PathSafety``.
"""

from __future__ import annotations

import shutil
from abc import ABC, abstractmethod
from pathlib import Path
from typing import List, Optional, Union

from .path_safety import PathSafety
from .exceptions import PathSafetyError


class VaultBackend(ABC):
    """Abstract vault access contract."""

    @abstractmethod
    def exists(self, path: Union[str, Path]) -> bool: ...

    @abstractmethod
    def read_text(self, path: Union[str, Path]) -> str: ...

    @abstractmethod
    def write_text(self, path: Union[str, Path], content: str) -> None: ...

    @abstractmethod
    def list_dir(self, path: Union[str, Path]) -> List[str]: ...

    @abstractmethod
    def mkdir(self, path: Union[str, Path]) -> None: ...

    @abstractmethod
    def remove(self, path: Union[str, Path]) -> None: ...

    @abstractmethod
    def move(self, src: Union[str, Path], dst: Union[str, Path]) -> None: ...

    @abstractmethod
    def walk(self, path: Union[str, Path]) -> List[str]: ...


class FilesystemBackend(VaultBackend):
    """Disk-backed implementation using PathSafety-guarded operations."""

    def __init__(self, safety: PathSafety) -> None:
        self.safety = safety

    def exists(self, path: Union[str, Path]) -> bool:
        try:
            return self.safety.validate(path).exists()
        except PathSafetyError:
            return False

    def read_text(self, path: Union[str, Path]) -> str:
        p = self.safety.validate(path)
        if not p.is_file():
            raise FileNotFoundError(str(p))
        return p.read_text(encoding="utf-8")

    def write_text(self, path: Union[str, Path], content: str) -> None:
        p = self.safety.validate(path)
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(content, encoding="utf-8")

    def list_dir(self, path: Union[str, Path]) -> List[str]:
        p = self.safety.validate(path)
        if not p.exists():
            return []
        return [str(Path(path).resolve() / c) for c in sorted(p.iterdir())]

    def mkdir(self, path: Union[str, Path]) -> None:
        p = self.safety.validate(path)
        p.mkdir(parents=True, exist_ok=True)

    def remove(self, path: Union[str, Path]) -> None:
        p = self.safety.validate(path)
        if p.is_dir():
            shutil.rmtree(p)
        elif p.exists():
            p.unlink()

    def move(self, src: Union[str, Path], dst: Union[str, Path]) -> None:
        s = self.safety.validate(src)
        d = self.safety.validate(dst)
        d.parent.mkdir(parents=True, exist_ok=True)
        shutil.move(str(s), str(d))

    def walk(self, path: Union[str, Path]) -> List[str]:
        p = self.safety.validate(path)
        if not p.exists():
            return []
        return [str(f) for f in sorted(p.rglob("*"))]
