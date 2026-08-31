"""OHSC skills system.

Skills are reusable procedures and knowledge that agents can invoke
instead of reinventing logic. Each skill has a name, description, version
and a ``run`` callable. They are discoverable and documented.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Callable, Dict, List


@dataclass
class Skill:
    name: str
    description: str
    version: str = "1.0.0"
    callable: Callable = None
    tags: List[str] = field(default_factory=list)

    def run(self, *a, **kw):
        if self.callable is None:
            raise NotImplementedError(f"Skill '{self.name}' has no callable.")
        return self.callable(*a, **kw)


def _read_frontmatter(text: str):
    if text.startswith("---"):
        end = text.find("\n---", 3)
        if end != -1:
            fm = text[3:end].strip()
            body = text[end + 4:]
            return fm, body
    return "", text


def _write_frontmatter(fm: str, body: str) -> str:
    if fm:
        return "---\n" + fm + "\n---\n" + body
    return body


def _extract_wikilinks(text: str) -> List[str]:
    import re
    return re.findall(r"\[\[([^\]\|]+)(?:\|[^\]]+)?\]\]", text)


def _safe_add_related_section(body: str, links: List[str]) -> str:
    """Append a '## Related Notes' section without duplicating existing links.

    Preserves all existing content. If a Related section already exists, only
    missing links are appended to it.
    """
    existing = set(_extract_wikilinks(body))
    new_links = [l for l in links if l.split("|")[0] not in existing]
    if not new_links:
        return body  # nothing to add, no change
    block = "\n".join("- [[" + l + "]]" for l in new_links)
    if "## Related Notes" in body or "## Related" in body:
        return body.rstrip() + "\n\n" + block + "\n"
    return body.rstrip() + "\n\n## Related Notes\n\n" + block + "\n"


# ---- registered skills -------------------------------------------------
_SKILLS: Dict[str, Skill] = {}


def _register(s: Skill) -> Skill:
    _SKILLS[s.name] = s
    return s


register_frontmatter = _register(Skill(
    name="frontmatter_rw",
    description="Read/write YAML frontmatter safely, preserving body.",
    tags=["metadata", "notes"],
    callable=None,
))

register_wikilinks = _register(Skill(
    name="wikilink_extract",
    description="Extract [[wikilinks]] (target note names) from markdown text.",
    tags=["linking", "graph"],
    callable=_extract_wikilinks,
))

register_add_related = _register(Skill(
    name="add_related_section",
    description=(
        "Add a '## Related Notes' section of wikilinks to a note body without "
        "duplicating existing links and without touching other content. Used by "
        "the linking_agent / MOC builder to grow a semantic Obsidian graph."
    ),
    version="1.1.0",
    tags=["linking", "graph", "moc"],
    callable=_safe_add_related_section,
))


def get_skill(name: str) -> Skill:
    return _SKILLS.get(name)


def list_skills() -> List[Skill]:
    return list(_SKILLS.values())


__all__ = [
    "Skill", "get_skill", "list_skills", "register_frontmatter",
    "register_wikilinks", "register_add_related",
]
