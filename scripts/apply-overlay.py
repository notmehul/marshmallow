#!/usr/bin/env python3
"""Preview or apply an approved Marshmallow overlay to a Claude Code skill."""

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
    apply_marker,
    backup_path,
    ensure_generated_skill_name,
    is_writable,
    normalize_skill_file,
    skill_id,
    unified_diff,
    validate_overlay,
)


def refuse_plugin_cache(path: Path) -> None:
    if "plugins" in path.parts and "cache" in path.parts:
        raise MarshmallowError("Refusing to edit a plugin cache. Create an aligned user-level copy instead.")


def record_apply(
    workspace_root: Path,
    source: Path,
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
        "source_skill": str(source),
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


def apply_overlay(
    workspace_root: Path,
    source: Path,
    overlay: Path,
    approve: bool,
    aligned_copy: Path | None,
) -> tuple[int, str]:
    ensure_workspace(workspace_root)
    source = normalize_skill_file(source)
    if not source.exists():
        raise MarshmallowError(f"Skill not found: {source}")
    validate_overlay(overlay)
    destination = normalize_skill_file(aligned_copy) if aligned_copy else source
    created_copy = destination != source and not destination.exists()
    if destination == source:
        refuse_plugin_cache(source)

    if destination == source and not is_writable(source):
        return 2, json.dumps(
            {
                "status": "read-only",
                "skill": str(source),
                "choices": [
                    "Create a personal aligned copy under ~/.claude/skills/<name>-aligned/.",
                    "Provide a writable skill path.",
                    "Skip this skill.",
                ],
            },
            indent=2,
        )

    before_bytes = destination.read_bytes() if destination.exists() else b""
    base = before_bytes.decode("utf-8") if destination.exists() else source.read_text(encoding="utf-8")
    overlay_store = workspace_root / "overlays" / f"{skill_id(destination)}.md"
    overlay_bytes = overlay.read_bytes()
    overlay_before_bytes = overlay_store.read_bytes() if overlay_store.exists() else b""
    updated = apply_marker(base, overlay_store)
    if destination != source:
        updated = ensure_generated_skill_name(updated, destination.parent.name)
    before = before_bytes.decode("utf-8")
    diff = unified_diff(destination, before, updated)
    diff += unified_diff(
        overlay_store,
        overlay_before_bytes.decode("utf-8"),
        overlay_bytes.decode("utf-8"),
    )
    if not approve:
        return 0, diff

    refuse_plugin_cache(destination)
    if before == updated and overlay_before_bytes == overlay_bytes:
        return 0, json.dumps({"status": "unchanged", "target": str(destination)}, indent=2)
    backup: Path | None = None
    overlay_backup: Path | None = None
    if destination.exists():
        backup = backup_path(workspace_root, destination)
        atomic_write(backup, destination.read_bytes())
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
    record_apply(
        workspace_root=workspace_root,
        source=source,
        target=destination,
        overlay_store=overlay_store,
        backup=backup,
        overlay_backup=overlay_backup,
        original_hash=sha256_bytes(before.encode("utf-8")),
        applied_hash=sha256_file(destination),
        overlay_original_hash=sha256_bytes(overlay_before_bytes),
        overlay_applied_hash=sha256_file(overlay_store),
        created_copy=created_copy,
    )
    result = {
        "status": "applied",
        "target": str(destination),
        "backup": str(backup) if backup else None,
        "created_copy": created_copy,
    }
    return 0, json.dumps(result, indent=2)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("skill", type=Path)
    parser.add_argument("overlay", type=Path)
    parser.add_argument("--workspace", type=Path, default=default_workspace())
    parser.add_argument("--approve", action="store_true")
    parser.add_argument("--aligned-copy", type=Path)
    args = parser.parse_args()
    try:
        code, message = apply_overlay(
            workspace_root=args.workspace.expanduser(),
            source=args.skill.expanduser(),
            overlay=args.overlay.expanduser(),
            approve=args.approve,
            aligned_copy=args.aligned_copy.expanduser() if args.aligned_copy else None,
        )
    except MarshmallowError as error:
        print(f"ERROR: {error}")
        return 1
    print(message)
    return code


if __name__ == "__main__":
    raise SystemExit(main())
