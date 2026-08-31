"""Input/contract validation utilities."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Union

from .contracts import OpClass, Task
from .exceptions import ValidationError


def validate_task(task: Task) -> None:
    if not task.agent:
        raise ValidationError("Task.agent must be set.")
    if not task.action:
        raise ValidationError("Task.action must be set.")
    if task.op_class not in (OpClass.READ, OpClass.WRITE, OpClass.DESTRUCTIVE):
        raise ValidationError(f"Invalid op_class: {task.op_class}")
    if task.op_class == OpClass.DESTRUCTIVE and not task.authorized:
        raise ValidationError(
            "Destructive task requires task.authorized=True."
        )


def validate_note_name(name: str) -> str:
    name = (name or "").strip()
    if not name:
        raise ValidationError("Note name must be non-empty.")
    # Obsidian note names map to file names; forbid path separators.
    for bad in ("/", "\\", ".."):
        if bad in name:
            raise ValidationError(f"Note name contains invalid char: {bad!r}")
    return name


def validate_is_markdown(path: Union[str, Path]) -> Path:
    p = Path(path)
    if p.suffix.lower() != ".md":
        raise ValidationError(f"Expected a Markdown file, got: {p}")
    return p


def non_empty(value: Any, field_name: str) -> Any:
    if value is None or value == "":
        raise ValidationError(f"{field_name} must not be empty.")
    return value
