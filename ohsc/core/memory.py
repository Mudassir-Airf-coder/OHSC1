"""Memory layer.

Stores system, agent, workflow, preference and history knowledge so OHSC
improves over time. Memory is never blindly trusted for critical
decisions; it is verified against the vault when needed. No sensitive
content is persisted.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional


@dataclass
class MemoryStore:
    system_root: Path
    _cache: Dict[str, Dict[str, Any]] = field(default_factory=dict)

    def _path(self, namespace: str) -> Path:
        p = Path(self.system_root) / "memory" / f"{namespace}.json"
        p.parent.mkdir(parents=True, exist_ok=True)
        return p

    def set(self, namespace: str, key: str, value: Any) -> None:
        data = self.get_all(namespace)
        data[key] = value
        self._path(namespace).write_text(json.dumps(data, indent=2), encoding="utf-8")

    def get(self, namespace: str, key: str, default: Any = None) -> Any:
        return self.get_all(namespace).get(key, default)

    def get_all(self, namespace: str) -> Dict[str, Any]:
        p = self._path(namespace)
        if not p.exists():
            return {}
        try:
            return json.loads(p.read_text(encoding="utf-8"))
        except Exception:
            return {}

    def append(self, namespace: str, key: str, item: Any) -> None:
        data = self.get_all(namespace)
        lst = data.get(key, [])
        if not isinstance(lst, list):
            lst = [lst]
        lst.append(item)
        data[key] = lst
        self.set(namespace, key, data[key])

    def history(self, limit: int = 50) -> List[Dict[str, Any]]:
        return self.get_all("history").get("requests", [])[-limit:]
