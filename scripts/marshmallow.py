#!/usr/bin/env python3
"""One public CLI for Marshmallow filesystem operations."""

from __future__ import annotations

import argparse
import json
import platform
import shutil
import sys
from pathlib import Path

from harness_adapter import (
    adapter_status,
    default_claude_md,
    default_target_for,
    harness_style,
    update_adapter,
)
from markdown_graph import graph_nodes, source_cards, validate_workspace
from marshmallow_workspace import MarshmallowError, default_workspace, ensure_workspace
from skill_overlay import apply_overlay, create_starter_skill, rollback_overlay
from skill_scanner import discover


def add_workspace(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--workspace", type=Path, default=default_workspace(), help="Marshmallow home directory.")


def json_print(payload: object) -> None:
    print(json.dumps(payload, indent=2, sort_keys=True))


def command_init(args: argparse.Namespace) -> int:
    root = ensure_workspace(args.workspace)
    json_print(
        {
            "status": "ready",
            "workspace": str(root),
            "created_or_verified": ["runtime.md", "inbox", "sources", "graph", "overlays", "backups"],
        }
    )
    return 0


def command_doctor(args: argparse.Namespace) -> int:
    root = ensure_workspace(args.workspace)
    errors = validate_workspace(root)

    def status_for(target: Path) -> dict[str, str]:
        try:
            return {"target": str(target), "status": adapter_status(target)}
        except MarshmallowError as error:
            return {"target": str(target), "status": "error", "error": str(error)}

    adapter = status_for(args.claude_md)
    harnesses = {
        "claude": status_for(args.claude_md),
        "codex": status_for(args.home / ".codex" / "AGENTS.md"),
        "cursor": status_for(args.project / "AGENTS.md"),
    }
    skills = discover(args.home, args.project, args.additional or [])
    try:
        sources = source_cards(root)
        nodes = graph_nodes(root)
    except MarshmallowError:
        sources = {}
        nodes = {}
    report = {
        "workspace": str(root),
        "workspace_status": "ok" if not errors else "error",
        "errors": errors,
        "runtime_exists": (root / "runtime.md").is_file(),
        "directories": {name: (root / name).is_dir() for name in ("inbox", "sources", "graph", "overlays", "backups")},
        "counts": {
            "sources": len(sources),
            "graph_nodes": len(nodes),
            "overlays": len(list((root / "overlays").glob("*.md"))),
            "backups": len(list((root / "backups").glob("**/record.json"))),
        },
        "adapter": adapter,
        "harnesses": harnesses,
        "skills_found": len(skills),
        "recommended_skills": sum(1 for skill in skills if skill["recommended"]),
        "python": platform.python_version(),
        "claude_cli": shutil.which("claude") or "not-found",
    }
    if args.json:
        json_print(report)
    else:
        print(f"Workspace: {report['workspace_status']} ({root})")
        print(f"Runtime: {'present' if report['runtime_exists'] else 'missing'}")
        print(f"Graph: {report['counts']['graph_nodes']} nodes from {report['counts']['sources']} sources")
        for name, info in harnesses.items():
            print(f"Adapter ({name}): {info['status']} ({info['target']})")
        print(f"Skills: {report['skills_found']} found, {report['recommended_skills']} recommended")
        for error in errors:
            print(f"ERROR: {error}")
    any_adapter_error = any(info.get("status") == "error" for info in harnesses.values())
    return 0 if not errors and not any_adapter_error else 1


def command_scan_skills(args: argparse.Namespace) -> int:
    json_print(discover(args.home, args.project, args.additional or []))
    return 0


def command_adapter(args: argparse.Namespace) -> int:
    action = args.action
    remove = action == "remove"
    approve = action == "apply" or (remove and args.approve)
    style = harness_style(args.harness)
    target = args.target or default_target_for(args.harness)
    code, message = update_adapter(args.workspace, target, approve=approve, remove=remove, style=style)
    print(message)
    return code


def command_overlay(args: argparse.Namespace) -> int:
    if args.action == "rollback":
        code, message = rollback_overlay(args.workspace, args.skill, approve=args.approve, force=args.force)
    else:
        if args.overlay is None:
            raise MarshmallowError("overlay preview/apply requires --overlay")
        code, message = apply_overlay(
            workspace_root=args.workspace,
            skill=args.skill,
            overlay=args.overlay,
            approve=args.action == "apply",
            aligned_copy=args.aligned_copy,
            target=args.target,
        )
    print(message)
    return code


def command_starter(args: argparse.Namespace) -> int:
    code, message = create_starter_skill(
        workspace_root=args.workspace,
        name=args.name,
        overlay=args.overlay,
        approve=args.action == "apply",
        target=args.target,
    )
    print(message)
    return code


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Marshmallow personalization workspace CLI.")
    subparsers = parser.add_subparsers(dest="command", required=True)

    init = subparsers.add_parser("init", help="Create the lightweight Marshmallow workspace.")
    add_workspace(init)
    init.set_defaults(func=command_init)

    doctor = subparsers.add_parser("doctor", help="Report workspace, adapter, graph, and skill health.")
    add_workspace(doctor)
    doctor.add_argument("--claude-md", type=Path, default=default_claude_md())
    doctor.add_argument("--home", type=Path, default=Path.home())
    doctor.add_argument("--project", type=Path, default=Path.cwd())
    doctor.add_argument("--additional", type=Path, action="append", default=[])
    doctor.add_argument("--json", action="store_true")
    doctor.set_defaults(func=command_doctor)

    scan = subparsers.add_parser("scan-skills", help="Find local Claude skills that may benefit from tuning.")
    add_workspace(scan)
    scan.add_argument("--home", type=Path, default=Path.home())
    scan.add_argument("--project", type=Path, default=Path.cwd())
    scan.add_argument("--additional", type=Path, action="append", default=[])
    scan.set_defaults(func=command_scan_skills)

    adapter = subparsers.add_parser("adapter", help="Preview, apply, or remove the Claude runtime adapter.")
    add_workspace(adapter)
    adapter.add_argument("action", choices=("preview", "apply", "remove"))
    adapter.add_argument(
        "--harness",
        choices=("claude", "codex", "cursor"),
        default="claude",
        help="Target harness. claude imports runtime.md from CLAUDE.md; codex/cursor add a pointer block to AGENTS.md.",
    )
    adapter.add_argument("--target", type=Path, help="Override the adapter target file (defaults to the harness location).")
    adapter.add_argument("--approve", action="store_true", help="Apply adapter removal after previewing it.")
    adapter.set_defaults(func=command_adapter)

    overlay = subparsers.add_parser("overlay", help="Preview, apply, or rollback a skill overlay.")
    add_workspace(overlay)
    overlay.add_argument("action", choices=("preview", "apply", "rollback"))
    overlay.add_argument("--skill", type=Path, required=True)
    overlay.add_argument("--overlay", type=Path)
    overlay.add_argument("--target", type=Path)
    overlay.add_argument("--aligned-copy", action="store_true")
    overlay.add_argument("--approve", action="store_true", help="Apply rollback after previewing it.")
    overlay.add_argument("--force", action="store_true", help="Rollback despite a changed target hash.")
    overlay.set_defaults(func=command_overlay)

    starter = subparsers.add_parser("starter", help="Preview or create a starter aligned skill.")
    add_workspace(starter)
    starter.add_argument("action", choices=("preview", "apply"))
    starter.add_argument("--overlay", type=Path, required=True)
    starter.add_argument("--name", default="marshmallow-aligned-builder")
    starter.add_argument("--target", type=Path)
    starter.set_defaults(func=command_starter)

    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        return args.func(args)
    except (MarshmallowError, OSError) as error:
        print(f"ERROR: {error}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
