#!/usr/bin/env python3
"""Preview or create a user-level starter skill backed by Marshmallow alignment."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from marshmallow_workspace import (
    MarshmallowError,
    atomic_write,
    default_workspace,
    ensure_workspace,
    read_workspace,
    sha256_bytes,
    sha256_file,
    timestamp,
    write_workspace,
)
from skill_overlay import (
    ID_PATTERN,
    alignment_block,
    apply_marker,
    backup_path,
    is_writable,
    normalize_skill_file,
    unified_diff,
    validate_overlay,
)


def default_target(name: str) -> Path:
    return Path.home() / ".claude" / "skills" / name / "SKILL.md"


def refuse_plugin_cache(path: Path) -> None:
    if "plugins" in path.parts and "cache" in path.parts:
        raise MarshmallowError("Refusing to create or update a plugin cache skill")


def starter_text(name: str, overlay_store: Path) -> str:
    return f"""---
name: {name}
description: Apply Marshmallow personal alignment to judgment-sensitive builder work.
---

# Marshmallow Aligned Builder

Use this skill for product, design, architecture, writing, planning, and review work where personal judgment should change useful defaults.

Preserve correctness, project instructions, and the user's current request. Use Marshmallow only to adapt taste, quality bars, anti-patterns, and decision rules.

{alignment_block(overlay_store)}
"""


def record_creation(
    workspace_root: Path,
    target: Path,
    overlay_store: Path,
    backup: Path | None,
    overlay_backup: Path | None,
    original_hash: str,
    applied_hash: str,
    overlay_original_hash: str,
    overlay_applied_hash: str,
    created_copy: bool,
) -> None:
    workspace = read_workspace(workspace_root)
    record = {
        "timestamp": timestamp(),
        "source_skill": str(target),
        "target_skill": str(target),
        "overlay_path": str(overlay_store),
        "backup_path": str(backup) if backup else None,
        "overlay_backup_path": str(overlay_backup) if overlay_backup else None,
        "original_hash": original_hash,
        "applied_hash": applied_hash,
        "overlay_original_hash": overlay_original_hash,
        "overlay_applied_hash": overlay_applied_hash,
        "created_copy": created_copy,
    }
    workspace["overlay_paths"][str(target)] = str(overlay_store)
    workspace["tuned_skills"][str(target)] = record
    workspace["backup_records"].append(record)
    write_workspace(workspace_root, workspace)


def create_starter_skill(
    workspace_root: Path,
    name: str,
    overlay: Path,
    target: Path | None,
    approve: bool,
) -> tuple[int, str]:
    if not ID_PATTERN.match(name):
        raise MarshmallowError(f"Starter skill name must use lowercase hyphen-case: {name!r}")
    ensure_workspace(workspace_root)
    validate_overlay(overlay)
    destination = normalize_skill_file(target or default_target(name))
    refuse_plugin_cache(destination)
    if destination.exists() and not is_writable(destination):
        return 2, json.dumps(
            {
                "status": "read-only",
                "skill": str(destination),
                "choices": [
                    "Provide a writable starter skill path.",
                    "Choose a different starter skill name.",
                    "Skip the starter skill and use the persistent adapter only.",
                ],
            },
            indent=2,
        )

    created_copy = not destination.exists()
    before_bytes = destination.read_bytes() if destination.exists() else b""
    before = before_bytes.decode("utf-8")
    overlay_store = workspace_root / "overlays" / f"{name}.md"
    overlay_bytes = overlay.read_bytes()
    overlay_before_bytes = overlay_store.read_bytes() if overlay_store.exists() else b""
    updated = starter_text(name, overlay_store) if created_copy else apply_marker(before, overlay_store)
    diff = unified_diff(destination, before, updated)
    diff += unified_diff(
        overlay_store,
        overlay_before_bytes.decode("utf-8"),
        overlay_bytes.decode("utf-8"),
    )
    if not approve:
        return 0, diff

    if before == updated and overlay_before_bytes == overlay_bytes:
        return 0, json.dumps({"status": "unchanged", "target": str(destination)}, indent=2)
    backup: Path | None = None
    overlay_backup: Path | None = None
    if destination.exists():
        backup = backup_path(workspace_root, destination)
        atomic_write(backup, before_bytes)
    if overlay_store.exists():
        overlay_backup = (backup or backup_path(workspace_root, destination)).with_name("overlay.md")
        atomic_write(overlay_backup, overlay_before_bytes)
    atomic_write(overlay_store, overlay_bytes)
    try:
        atomic_write(destination, updated)
    except OSError:
        if overlay_backup:
            atomic_write(overlay_store, overlay_backup.read_bytes())
        else:
            overlay_store.unlink(missing_ok=True)
        raise
    record_creation(
        workspace_root=workspace_root,
        target=destination,
        overlay_store=overlay_store,
        backup=backup,
        overlay_backup=overlay_backup,
        original_hash=sha256_bytes(before_bytes),
        applied_hash=sha256_file(destination),
        overlay_original_hash=sha256_bytes(overlay_before_bytes),
        overlay_applied_hash=sha256_file(overlay_store),
        created_copy=created_copy,
    )
    return 0, json.dumps(
        {"status": "applied", "target": str(destination), "backup": str(backup) if backup else None, "created_copy": created_copy},
        indent=2,
    )


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("overlay", type=Path)
    parser.add_argument("--workspace", type=Path, default=default_workspace())
    parser.add_argument("--name", default="marshmallow-aligned-builder")
    parser.add_argument("--target", type=Path)
    parser.add_argument("--approve", action="store_true")
    args = parser.parse_args()
    try:
        code, message = create_starter_skill(
            workspace_root=args.workspace.expanduser(),
            name=args.name,
            overlay=args.overlay.expanduser(),
            target=args.target.expanduser() if args.target else None,
            approve=args.approve,
        )
    except MarshmallowError as error:
        print(f"ERROR: {error}")
        return 1
    print(message)
    return code


if __name__ == "__main__":
    raise SystemExit(main())
