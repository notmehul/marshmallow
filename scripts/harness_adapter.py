#!/usr/bin/env python3
"""Reversible user-level Claude Code adapter installation."""

from __future__ import annotations

import difflib
import json
from pathlib import Path

from marshmallow_workspace import (
    MarshmallowError,
    atomic_write,
    ensure_workspace,
    sha256_bytes,
    sha256_file,
    timestamp,
    write_record,
)

START_MARKER = "<!-- marshmallow:adapter:start -->"
END_MARKER = "<!-- marshmallow:adapter:end -->"


def is_writable(path: Path) -> bool:
    return bool(path.stat().st_mode & 0o222)


def default_claude_md() -> Path:
    return Path.home() / ".claude" / "CLAUDE.md"


def adapter_block(runtime_path: Path) -> str:
    return f"{START_MARKER}\n@{runtime_path.resolve()}\n{END_MARKER}"


def install_marker(original: str, runtime_path: Path) -> str:
    block = adapter_block(runtime_path)
    if START_MARKER not in original and END_MARKER not in original:
        prefix = original.rstrip()
        return f"{prefix}\n\n{block}\n" if prefix else f"{block}\n"
    validate_marker(original)
    start = original.index(START_MARKER)
    end = original.index(END_MARKER) + len(END_MARKER)
    return original[:start].rstrip() + "\n\n" + block + original[end:].rstrip() + "\n"


def remove_marker(original: str) -> str:
    if START_MARKER not in original and END_MARKER not in original:
        return original
    validate_marker(original)
    start = original.index(START_MARKER)
    end = original.index(END_MARKER) + len(END_MARKER)
    before = original[:start].rstrip()
    after = original[end:].lstrip()
    if before and after:
        return f"{before}\n\n{after}"
    if before:
        return f"{before}\n"
    return after


def validate_marker(text: str) -> None:
    if text.count(START_MARKER) != 1 or text.count(END_MARKER) != 1:
        raise MarshmallowError("CLAUDE.md contains malformed or duplicate Marshmallow adapter markers")
    if text.index(START_MARKER) > text.index(END_MARKER):
        raise MarshmallowError("CLAUDE.md contains reversed Marshmallow adapter markers")


def adapter_record_dir(root: Path) -> Path:
    base = root / "backups" / "adapters" / timestamp()
    if not base.exists():
        return base
    counter = 2
    while True:
        candidate = base.with_name(f"{base.name}-{counter}")
        if not candidate.exists():
            return candidate
        counter += 1


def unified_diff(target: Path, original: str, updated: str) -> str:
    return "".join(
        difflib.unified_diff(
            original.splitlines(keepends=True),
            updated.splitlines(keepends=True),
            fromfile=str(target),
            tofile=str(target),
        )
    )


def adapter_status(target: Path) -> str:
    if not target.exists():
        return "missing"
    text = target.read_text(encoding="utf-8")
    if START_MARKER in text or END_MARKER in text:
        validate_marker(text)
        return "installed"
    return "not-installed"


def update_adapter(workspace_root: Path, target: Path, approve: bool, remove: bool) -> tuple[int, str]:
    workspace_root = ensure_workspace(workspace_root)
    target = target.expanduser()
    if target.exists() and not is_writable(target):
        raise MarshmallowError(f"Claude adapter target is read-only: {target}")
    original_bytes = target.read_bytes() if target.exists() else b""
    original = original_bytes.decode("utf-8")
    updated = remove_marker(original) if remove else install_marker(original, workspace_root / "runtime.md")
    diff = unified_diff(target, original, updated)
    action = "remove" if remove else "install"
    if not approve:
        return 0, diff or json.dumps({"status": "unchanged", "action": action}, indent=2)
    if updated == original:
        return 0, json.dumps({"status": "unchanged", "action": action}, indent=2)

    record_dir = adapter_record_dir(workspace_root)
    backup: Path | None = None
    if target.exists():
        backup = record_dir / "CLAUDE.md"
        atomic_write(backup, original_bytes)
    record = {
        "timestamp": timestamp(),
        "action": action,
        "target": str(target.resolve()),
        "backup_path": str(backup.resolve()) if backup else None,
        "original_hash": sha256_bytes(original_bytes),
        "planned_hash": sha256_bytes(updated.encode("utf-8")),
    }
    write_record(record_dir / "record.json", record)

    atomic_write(target, updated)
    record["applied_hash"] = sha256_file(target)
    write_record(record_dir / "record.json", record)
    return 0, json.dumps(
        {
            "status": "applied",
            "action": action,
            "target": str(target),
            "backup": str(backup) if backup else None,
            "record": str(record_dir / "record.json"),
        },
        indent=2,
    )
