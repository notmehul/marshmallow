#!/usr/bin/env python3
"""Preview or apply rollback of the latest Marshmallow skill update."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from marshmallow_workspace import (
    MarshmallowError,
    atomic_write,
    default_workspace,
    read_workspace,
    sha256_file,
    write_workspace,
)
from skill_overlay import normalize_skill_file


def latest_record(workspace: dict, target: Path) -> dict:
    matches = matching_records(workspace, target)
    if not matches:
        raise MarshmallowError(f"No Marshmallow backup record for {target}")
    return matches[-1]


def matching_records(workspace: dict, target: Path) -> list[dict]:
    return [
        record
        for record in workspace.get("backup_records", [])
        if Path(record["target_skill"]) == target
    ]


def rollback(workspace_root: Path, target: Path, approve: bool, force: bool) -> tuple[int, str]:
    target = normalize_skill_file(target)
    workspace = read_workspace(workspace_root)
    record = latest_record(workspace, target)
    if not target.exists():
        raise MarshmallowError(f"Tuned skill no longer exists: {target}")
    if sha256_file(target) != record["applied_hash"] and not force:
        raise MarshmallowError("Skill changed after Marshmallow tuning. Re-run with --force only after reviewing the file.")
    overlay = Path(record["overlay_path"])
    if record.get("overlay_applied_hash") and (
        not overlay.exists() or sha256_file(overlay) != record["overlay_applied_hash"]
    ) and not force:
        raise MarshmallowError("Canonical overlay changed after Marshmallow tuning. Re-run with --force only after reviewing the file.")
    action = "delete generated aligned copy" if record["created_copy"] else "restore backup"
    if not approve:
        return 0, json.dumps({"status": "preview", "target": str(target), "action": action}, indent=2)

    if record["created_copy"]:
        target.unlink()
        try:
            target.parent.rmdir()
        except OSError:
            pass
    else:
        backup = Path(record["backup_path"])
        if not backup.exists():
            raise MarshmallowError(f"Backup missing: {backup}")
        atomic_write(target, backup.read_bytes())
    overlay_backup = record.get("overlay_backup_path")
    if overlay_backup:
        atomic_write(overlay, Path(overlay_backup).read_bytes())
    elif record.get("overlay_applied_hash") and overlay.exists():
        overlay.unlink()
    workspace["backup_records"].remove(record)
    previous_records = matching_records(workspace, target)
    if previous_records and target.exists():
        previous = previous_records[-1]
        workspace["tuned_skills"][str(target)] = previous
        workspace["overlay_paths"][str(target)] = previous["overlay_path"]
    else:
        workspace["tuned_skills"].pop(str(target), None)
        workspace["overlay_paths"].pop(str(target), None)
    write_workspace(workspace_root, workspace)
    return 0, json.dumps({"status": "rolled-back", "target": str(target), "action": action}, indent=2)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("skill", type=Path)
    parser.add_argument("--workspace", type=Path, default=default_workspace())
    parser.add_argument("--approve", action="store_true")
    parser.add_argument("--force", action="store_true")
    args = parser.parse_args()
    try:
        code, message = rollback(
            args.workspace.expanduser(),
            args.skill.expanduser(),
            args.approve,
            args.force,
        )
    except MarshmallowError as error:
        print(f"ERROR: {error}")
        return 1
    print(message)
    return code


if __name__ == "__main__":
    raise SystemExit(main())
