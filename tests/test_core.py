"""Unit tests for core safety, permissions, validation, transactions."""

from __future__ import annotations

import pytest
from pathlib import Path

from ohsc.core.path_safety import PathSafety
from ohsc.core.exceptions import PathSafetyError
from ohsc.core.permissions import PermissionAgent
from ohsc.core.validation import validate_note_name, validate_task
from ohsc.core.contracts import Task, OpClass
from ohsc.core.transaction_agent import TransactionAgent


def test_path_safety_blocks_traversal():
    safety = PathSafety([r"D:\HOSC", r"D:\Mudassir database"])
    # Allowed vault file
    p = safety.validate(r"D:\Mudassir database\Note.md")
    assert p.name == "Note.md"
    # Traversal attempt
    with pytest.raises(PathSafetyError):
        safety.validate(r"D:\Mudassir database\..\Windows\secret.txt")
    # Outside allowed roots
    with pytest.raises(PathSafetyError):
        safety.validate(r"C:\Users\HAJI LAPTOP G55\secret.txt")


def test_permissions_classify():
    pa = PermissionAgent()
    assert pa.classify("search") == OpClass.READ
    assert pa.classify("create") == OpClass.WRITE
    assert pa.classify("delete") == OpClass.DESTRUCTIVE
    # Destructive blocked without auth
    dec = pa.decide("delete", user_authorized=False)
    assert dec.authorized is False
    dec2 = pa.decide("delete", user_authorized=True)
    assert dec2.authorized is True


def test_validate_note_name_rejects_separators():
    assert validate_note_name("My Note") == "My Note"
    with pytest.raises(Exception):
        validate_note_name("a/b")
    with pytest.raises(Exception):
        validate_note_name("..")


def test_validate_task_blocks_unauthorized_destructive():
    t = Task(agent="note_agent", action="delete", op_class=OpClass.DESTRUCTIVE,
             authorized=False)
    with pytest.raises(Exception):
        validate_task(t)


def test_transaction_rollback(tmp_path):
    # Build a minimal runtime-like harness for the transaction agent.
    from ohsc.config import SystemConfig
    cfg = SystemConfig(vault_root=tmp_path, system_root=tmp_path / "sys")
    from ohsc.core.runtime import Runtime
    rt = Runtime(cfg)
    # Execute that fails -> rollback restores original.
    f = tmp_path / "note.md"
    f.write_text("original", encoding="utf-8")

    def execute():
        f.write_text("changed", encoding="utf-8")
        raise RuntimeError("boom")

    def validate():
        return f.read_text(encoding="utf-8") == "changed"

    report = rt.transaction_agent.run(
        "test", [str(f)], execute, validate, reversible=True
    )
    assert report.success is False
    assert report.rolled_back is True
    assert f.read_text(encoding="utf-8") == "original"
