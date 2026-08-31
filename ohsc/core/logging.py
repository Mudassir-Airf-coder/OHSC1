"""Structured, rotating logging for OHSC.

Every important operation is recorded with: timestamp, task id, agent,
operation, target, result, duration, errors, validation and reviewer
results. Logs are rotated to avoid unbounded disk growth.
"""

from __future__ import annotations

import json
import logging
import logging.handlers
import threading
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

from ..config import load_config

_LOCK = threading.Lock()
_CONFIGURED = False


def configure_logging() -> None:
    """Configure the root OHSC logger with rotating file + console handlers."""
    global _CONFIGURED
    cfg = load_config()
    cfg.ensure_dirs()

    logger = logging.getLogger("ohsc")
    logger.setLevel(getattr(logging, cfg.log_level.upper(), logging.INFO))
    logger.handlers.clear()
    logger.propagate = False

    fmt = logging.Formatter(
        "%(asctime)s | %(levelname)s | %(name)s | %(message)s",
        datefmt="%Y-%m-%dT%H:%M:%S",
    )

    file_handler = logging.handlers.RotatingFileHandler(
        cfg.log_dir / "ohsc.log",
        maxBytes=cfg.log_max_bytes,
        backupCount=cfg.log_backups,
        encoding="utf-8",
    )
    file_handler.setFormatter(fmt)
    logger.addHandler(file_handler)

    console = logging.StreamHandler()
    console.setFormatter(fmt)
    logger.addHandler(console)

    _CONFIGURED = True


def get_logger(name: str = "ohsc") -> logging.Logger:
    if not _CONFIGURED:
        configure_logging()
    return logging.getLogger(name)


def _now() -> str:
    return datetime.utcnow().isoformat() + "Z"


def record_event(
    task_id: str,
    agent: str,
    operation: str,
    target: str,
    result: str,
    duration_ms: float = 0.0,
    errors: Optional[List[str]] = None,
    warnings: Optional[List[str]] = None,
    extra: Optional[Dict[str, Any]] = None,
) -> None:
    """Append a structured audit record to the audit log file."""
    cfg = load_config()
    cfg.ensure_dirs()
    record = {
        "timestamp": _now(),
        "task_id": task_id,
        "agent": agent,
        "operation": operation,
        "target": target,
        "result": result,
        "duration_ms": round(duration_ms, 2),
        "errors": errors or [],
        "warnings": warnings or [],
        "extra": extra or {},
    }
    with _LOCK:
        audit_path = cfg.log_dir / "audit.log"
        try:
            with audit_path.open("a", encoding="utf-8") as fh:
                fh.write(json.dumps(record, ensure_ascii=False) + "\n")
        except Exception:
            # Logging must never break the system.
            pass


def read_audit(limit: int = 200) -> List[Dict[str, Any]]:
    cfg = load_config()
    audit_path = cfg.log_dir / "audit.log"
    if not audit_path.exists():
        return []
    out: List[Dict[str, Any]] = []
    with audit_path.open("r", encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if not line:
                continue
            try:
                out.append(json.loads(line))
            except Exception:
                continue
    return out[-limit:]
