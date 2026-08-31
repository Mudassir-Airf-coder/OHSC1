"""Centralized configuration for OHSC.

This is the single source of truth for paths, safety mode, logging,
indexing, backup and testing configuration. No agent should hardcode
paths or configuration; they must import from here (or from a loaded
``SystemConfig`` instance).
"""

from __future__ import annotations

import json
import os
from dataclasses import dataclass, field, asdict
from pathlib import Path
from typing import Dict, List, Any

# ---------------------------------------------------------------------------
# Default, authoritative roots. These can be overridden by environment
# variables or a config file, but the defaults are deterministic.
# ---------------------------------------------------------------------------
DEFAULT_SYSTEM_ROOT = Path(r"D:\HOSC").resolve()
DEFAULT_VAULT_ROOT = Path(r"D:\Mudassir database").resolve()


def _env_path(name: str, default: Path) -> Path:
    val = os.environ.get(name)
    if val:
        return Path(val).resolve()
    return default


@dataclass
class SystemConfig:
    """Typed, central configuration object."""

    system_root: Path = field(default_factory=lambda: DEFAULT_SYSTEM_ROOT)
    vault_root: Path = field(default_factory=lambda: DEFAULT_VAULT_ROOT)
    allowed_roots: List[str] = field(default_factory=list)

    safety_mode: str = "strict"          # "strict" | "normal"
    dry_run_default: bool = False

    log_level: str = "INFO"
    log_dir: Path = field(default_factory=lambda: DEFAULT_SYSTEM_ROOT / "logs")
    log_max_bytes: int = 2_000_000
    log_backups: int = 5

    memory_dir: Path = field(default_factory=lambda: DEFAULT_SYSTEM_ROOT / "memory")
    index_enabled: bool = True
    index_dir: Path = field(default_factory=lambda: DEFAULT_SYSTEM_ROOT / "index")
    index_refresh_seconds: int = 30

    backup_enabled: bool = True
    backup_dir: Path = field(default_factory=lambda: DEFAULT_SYSTEM_ROOT / "snapshots")

    test_vault_root: Path = field(
        default_factory=lambda: DEFAULT_SYSTEM_ROOT / "tests" / "fixtures" / "test_vault"
    )
    require_explicit_destructive_auth: bool = True

    def __post_init__(self) -> None:
        # Coerce string paths that may arrive from JSON into Path objects.
        for attr in (
            "system_root", "vault_root", "log_dir", "memory_dir",
            "index_dir", "backup_dir", "test_vault_root",
        ):
            value = getattr(self, attr)
            if isinstance(value, str):
                setattr(self, attr, Path(value).resolve())
        if not self.allowed_roots:
            self.allowed_roots = [str(self.system_root), str(self.vault_root)]

    # -- serialization ----------------------------------------------------
    def to_dict(self) -> Dict[str, Any]:
        d = asdict(self)
        for k, v in list(d.items()):
            if isinstance(v, Path):
                d[k] = str(v)
        return d

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "SystemConfig":
        known = {f for f in cls.__dataclass_fields__}  # type: ignore[attr-defined]
        filtered = {k: v for k, v in data.items() if k in known}
        return cls(**filtered)

    def save(self, path: Path) -> None:
        path = Path(path)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(self.to_dict(), indent=2), encoding="utf-8")

    # -- helper accessors -------------------------------------------------
    @property
    def allowed_root_paths(self) -> List[Path]:
        return [Path(p).resolve() for p in self.allowed_roots]

    def ensure_dirs(self) -> None:
        """Create the base directories OHSC needs to operate."""
        for p in (
            self.system_root, self.log_dir, self.memory_dir,
            self.index_dir, self.backup_dir,
        ):
            p.mkdir(parents=True, exist_ok=True)


_CONFIG_PATH = DEFAULT_SYSTEM_ROOT / "config" / "ohsc.json"

# Singleton loaded configuration. Falls back to defaults when the file is
# missing or invalid so the system can always bootstrap itself.
CONFIG: SystemConfig


def _build_config() -> SystemConfig:
    cfg = SystemConfig()
    # Allow environment overrides for the two most important roots.
    cfg.system_root = _env_path("OHSC_SYSTEM_ROOT", cfg.system_root)
    cfg.vault_root = _env_path("OHSC_VAULT_ROOT", cfg.vault_root)
    cfg.allowed_roots = [str(cfg.system_root), str(cfg.vault_root)]

    if _CONFIG_PATH.exists():
        try:
            data = json.loads(_CONFIG_PATH.read_text(encoding="utf-8"))
            cfg = SystemConfig.from_dict({**cfg.to_dict(), **data})
        except Exception:
            # Never crash on a bad config file; keep safe defaults.
            pass
    cfg.__post_init__()
    return cfg


def load_config(reload: bool = False) -> SystemConfig:
    global CONFIG
    if reload or "CONFIG" not in globals():
        CONFIG = _build_config()
    return CONFIG


# Initialise on import.
load_config()
