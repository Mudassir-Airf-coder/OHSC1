"""OHSC session token helpers.

When a user runs ``ohsc run``, OHSC creates a short-lived local session
token. The token is printed once so the user can paste it into any AI
tool. The token is stored only under the OHSC system root (never in the
vault) and contains no vault content or API secrets.
"""

from __future__ import annotations

import json
import secrets
import time
from pathlib import Path
from typing import Any, Dict

from ..config import load_config


def _session_dir() -> Path:
    cfg = load_config()
    d = cfg.system_root / "memory" / "sessions"
    d.mkdir(parents=True, exist_ok=True)
    return d


def create_session_token(ttl_seconds: int = 60 * 60 * 12) -> Dict[str, Any]:
    """Create and persist a new session token. Returns public session info."""
    token = secrets.token_urlsafe(24)
    now = int(time.time())
    record = {
        "token": token,
        "created_at": now,
        "expires_at": now + ttl_seconds,
        "status": "active",
    }
    path = _session_dir() / f"{token[:12]}.json"
    path.write_text(json.dumps(record, indent=2), encoding="utf-8")
    return {
        "token": token,
        "created_at": now,
        "expires_at": record["expires_at"],
        "ttl_seconds": ttl_seconds,
        "skill_path": str(load_config().system_root / "skills" / "OHSC_AGENT_SKILL.md"),
        "activate_command": "ohsc activate",
        "capabilities_command": "ohsc capabilities --json",
        "agents_command": "ohsc agents --json",
    }


def validate_session_token(token: str) -> Dict[str, Any]:
    """Validate a session token. Returns status dict."""
    if not token or not isinstance(token, str):
        return {"valid": False, "reason": "empty"}
    path = _session_dir() / f"{token[:12]}.json"
    if not path.exists():
        return {"valid": False, "reason": "not_found"}
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {"valid": False, "reason": "corrupt"}
    if data.get("token") != token:
        return {"valid": False, "reason": "mismatch"}
    if int(time.time()) > int(data.get("expires_at", 0)):
        return {"valid": False, "reason": "expired"}
    if data.get("status") != "active":
        return {"valid": False, "reason": "inactive"}
    return {"valid": True, "expires_at": data.get("expires_at")}
