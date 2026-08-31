"""Vault Index implementation (continuation of indexing.py)."""

from __future__ import annotations

import json
import time
from pathlib import Path
from typing import Dict, List, Optional, Set

from .indexing import (
    NoteRecord, FRONTMATTER_RE, WIKILINK_RE, TAG_RE, parse_frontmatter,
)
from .filesystem import VaultBackend


class VaultIndex:
    """Incremental cache of vault metadata with on-disk persistence."""

    def __init__(self, backend: VaultBackend, index_dir: Path) -> None:
        self.backend = backend
        self.index_dir = Path(index_dir)
        self.index_dir.mkdir(parents=True, exist_ok=True)
        self.notes: Dict[str, NoteRecord] = {}
        self._mtimes: Dict[str, float] = {}
        self._loaded = False

    # -- persistence ------------------------------------------------------
    def _store_path(self) -> Path:
        return self.index_dir / "vault_index.json"

    def load(self) -> None:
        p = self._store_path()
        if p.exists():
            try:
                data = json.loads(p.read_text(encoding="utf-8"))
                for rec in data.get("notes", []):
                    self.notes[rec["path"]] = NoteRecord(**rec)
                    self._mtimes[rec["path"]] = rec.get("mtime", 0.0)
            except Exception:
                self.notes = {}
                self._mtimes = {}
        self._loaded = True

    def save(self) -> None:
        data = {
            "notes": [n.to_dict() for n in self.notes.values()],
            "updated_at": time.time(),
        }
        self._store_path().write_text(json.dumps(data, indent=2), encoding="utf-8")

    # -- refresh ----------------------------------------------------------
    def refresh(self, vault_root: Path, force: bool = False) -> int:
        """Incrementally re-scan the vault. Returns number of notes indexed."""
        if not self._loaded:
            self.load()
        root = Path(vault_root).resolve()
        changed = 0
        seen: Set[str] = set()
        for f in root.rglob("*.md"):
            try:
                rp = str(f.resolve())
            except Exception:
                continue
            if ".obsidian" in f.parts:
                continue
            seen.add(rp)
            mtime = f.stat().st_mtime
            if force or self._mtimes.get(rp, -1) != mtime or rp not in self.notes:
                text = self.backend.read_text(f)
                props, body = parse_frontmatter(text)
                tags = props.get("tags", [])
                if isinstance(tags, str):
                    tags = [t.strip() for t in tags.split(",") if t.strip()]
                links = WIKILINK_RE.findall(body)
                links = [l.split("|")[0].split("#")[0].strip() for l in links]
                rec = NoteRecord(
                    path=rp,
                    title=f.stem,
                    tags=list(tags),
                    properties={k: v for k, v in props.items() if k != "tags"},
                    links=links,
                    mtime=mtime,
                )
                self.notes[rp] = rec
                self._mtimes[rp] = mtime
                changed += 1
        for missing in [p for p in self.notes if p not in seen]:
            del self.notes[missing]
            self._mtimes.pop(missing, None)
            changed += 1
        self._build_backlinks()
        self.save()
        return changed

    def _build_backlinks(self) -> None:
        title_to_path: Dict[str, str] = {}
        for rec in self.notes.values():
            title_to_path[rec.title.lower()] = rec.path
        for rec in self.notes.values():
            rec.backlinks = []
        for rec in self.notes.values():
            for link in rec.links:
                target = title_to_path.get(link.lower())
                if target and target != rec.path:
                    self.notes[target].backlinks.append(rec.title)

    # -- queries ----------------------------------------------------------
    def get_note(self, title: str) -> Optional[NoteRecord]:
        key = title.lower()
        for rec in self.notes.values():
            if rec.title.lower() == key:
                return rec
        return None

    def search_text(self, query: str) -> List[NoteRecord]:
        q = query.lower()
        return [r for r in self.notes.values() if q in self.backend.read_text(r.path).lower()]

    def search_tag(self, tag: str) -> List[NoteRecord]:
        t = tag.lower().lstrip("#")
        return [r for r in self.notes.values() if t in [x.lower() for x in r.tags]]

    def orphans(self) -> List[NoteRecord]:
        return [r for r in self.notes.values() if not r.backlinks and not r.links]

    def hubs(self) -> List[NoteRecord]:
        return sorted(self.notes.values(), key=lambda r: -len(r.backlinks))[:10]
