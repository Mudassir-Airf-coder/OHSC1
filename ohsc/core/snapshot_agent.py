"""Snapshot / Backup agent.

Before high-risk operations, affected files are captured so the system
can recover. Snapshots are stored under ``D:\\HOSC\\snapshots`` and never
inside the vault.
"""

from __future__ import annotations

import json
import shutil
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Union

from .exceptions import OHSCError
from .filesystem import VaultBackend
from .agent_base import BaseAgent, AgentContract


@dataclass
class Snapshot:
    id: str
    created_at: float
    label: str
    files: Dict[str, str] = field(default_factory=dict)  # rel_path -> backup_path
    meta: Dict[str, object] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, object]:
        return {
            "id": self.id,
            "created_at": self.created_at,
            "label": self.label,
            "files": self.files,
            "meta": self.meta,
        }


class SnapshotAgent(BaseAgent):
    """Captures and restores vault file snapshots for safe recovery."""

    name = "snapshot_agent"
    role = "backup_snapshot"
    contract = AgentContract(
        name=name, role=role,
        responsibilities=["Capture affected files", "Restore from snapshot"],
        allowed_operations=["capture", "restore"],
        input_contract="list of paths + label",
        output_contract="Snapshot",
        dependencies=[],
    )

    def __init__(self, backend: VaultBackend, backup_dir: Path) -> None:
        super().__init__()
        self.backend = backend
        self.backup_dir = Path(backup_dir)
        self.backup_dir.mkdir(parents=True, exist_ok=True)

    def capture(self, paths: List[Union[str, Path]], label: str = "snapshot") -> Snapshot:
        snap_id = f"snap_{int(time.time()*1000)}_{len(paths)}"
        snap_dir = self.backup_dir / snap_id
        snap_dir.mkdir(parents=True, exist_ok=True)
        files: Dict[str, str] = {}
        for p in paths:
            src = Path(p)
            if src.is_file():
                rel = src.name
                dst = snap_dir / rel
                # Avoid clobbering identical names from different folders.
                if dst.exists():
                    rel = src.as_posix().replace("/", "_").lstrip("_")
                    dst = snap_dir / rel
                shutil.copy2(src, dst)
                files[str(src)] = str(dst)
        snap = Snapshot(id=snap_id, created_at=time.time(), label=label, files=files)
        (snap_dir / "manifest.json").write_text(
            json.dumps(snap.to_dict(), indent=2), encoding="utf-8"
        )
        return snap

    def restore(self, snap: Snapshot) -> None:
        for original, backup in snap.files.items():
            if Path(backup).exists():
                self.backend.write_text(original, Path(backup).read_text(encoding="utf-8"))

    def list_snapshots(self) -> List[str]:
        return sorted(p.name for p in self.backup_dir.iterdir() if p.is_dir())
