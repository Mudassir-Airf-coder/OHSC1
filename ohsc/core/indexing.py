"""Vault indexing layer.

Maintains an incremental index of files, frontmatter, tags, wikilinks and
backlinks. The index is a *cache* and is never treated as the
unquestioned source of truth; operations that need certainty re-read the
filesystem (see ``refresh`` / ``get_note``). Designed to avoid scanning
the whole vault on every request.
"""

from __future__ import annotations

import json
import re
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional, Set

from .filesystem import VaultBackend

FRONTMATTER_RE = re.compile(r"^---\n(.*?)\n---\n?", re.DOTALL)
WIKILINK_RE = re.compile(r"\[\[([^\]]+)\]\]")
TAG_RE = re.compile(r"(?:^|\s)#([A-Za-z0-9/_-]+)")


@dataclass
class NoteRecord:
    path: str
    title: str
    tags: List[str] = field(default_factory=list)
    properties: Dict[str, object] = field(default_factory=dict)
    links: List[str] = field(default_factory=list)
    backlinks: List[str] = field(default_factory=list)
    mtime: float = 0.0

    def to_dict(self) -> Dict[str, object]:
        return {
            "path": self.path, "title": self.title, "tags": self.tags,
            "properties": self.properties, "links": self.links,
            "backlinks": self.backlinks, "mtime": self.mtime,
        }


def parse_frontmatter(text: str):
    """Return (properties_dict, body_text)."""
    m = FRONTMATTER_RE.match(text)
    if not m:
        return {}, text
    block = m.group(1)
    props: Dict[str, object] = {}
    current_key = None
    current_list: List[str] = []
    for raw in block.splitlines():
        if not raw.strip():
            continue
        if raw.startswith("  - ") or raw.startswith("- "):
            current_list.append(raw.strip("- ").strip())
            continue
        mline = re.match(r"^([A-Za-z0-9_-]+):\s*(.*)$", raw)
        if mline:
            if current_key is not None:
                props[current_key] = current_list or props.get(current_key)
                current_list = []
            current_key = mline.group(1)
            val = mline.group(2).strip()
            if val:
                props[current_key] = _coerce(val)
    if current_key is not None:
        props[current_key] = current_list or props.get(current_key)
    body = text[m.end():]
    return props, body


def _coerce(val: str):
    if val.lower() in ("true", "false"):
        return val.lower() == "true"
    try:
        return int(val)
    except ValueError:
        return val
