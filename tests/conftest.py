"""OHSC test configuration and shared fixtures.

Tests run against an isolated temporary vault so the real user vault is
NEVER touched. Destructive tests are confined to that fixture.
"""

from __future__ import annotations

import sys
import tempfile
from pathlib import Path

# Make the package importable when pytest is run from D:\HOSC.
ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from ohsc.config import SystemConfig
from ohsc.system import build_runtime


def make_test_runtime() -> tuple:
    """Create a temp vault + runtime. Returns (runtime, tmp_path)."""
    tmp = Path(tempfile.mkdtemp(prefix="ohsc_test_"))
    vault = tmp / "vault"
    vault.mkdir()
    (vault / "Welcome.md").write_text(
        "Welcome! Link to [[Project Alpha]] and [[Project Beta]].\n#project",
        encoding="utf-8",
    )
    sys_root = tmp / "HOSC"
    cfg = SystemConfig(
        vault_root=vault, system_root=sys_root,
        log_dir=sys_root / "logs", memory_dir=sys_root / "memory",
        index_dir=sys_root / "index", backup_dir=sys_root / "snapshots",
        index_enabled=True,
    )
    rt = build_runtime(cfg)
    return rt, tmp


def cleanup(tmp):
    import shutil
    shutil.rmtree(tmp, ignore_errors=True)
