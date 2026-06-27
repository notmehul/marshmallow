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
from markdown_graph import (
    SCAFFOLD_KINDS,
    graph_nodes,
    graph_quality_warnings,
    index_pages,
    projections,
    scaffold_record,
    source_cards,
    validate_workspace,
)
from capture import list_candidates, promote, remember
from marshmallow_workspace import MarshmallowError, atomic_write, default_workspace, ensure_workspace, require_workspace
from recall import recall_context
from skill_overlay import apply_overlay, create_starter_skill, rollback_overlay
from skill_scanner import discover


def add_workspace(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--workspace", type=Path, default=default_workspace(), help="Marshmallow home directory.")


def json_print(payload: object) -> None:
    print(json.dumps(payload, indent=2, sort_keys=True))


def runtime_guidance_warnings(root: Path) -> list[str]:
    runtime = root / "runtime.md"
    if not runtime.exists():
        return []
    text = runtime.read_text(encoding="utf-8")
    expected = (
        "recall",
        "indexes/",
        "projections/",
        "Do not crawl the whole graph by default.",
    )
    if all(fragment in text for fragment in expected):
        return []
    return [f"{runtime}: runtime guidance may be stale; update it to use recall, check indexes first, and use projections as recall packets"]


def command_init(args: argparse.Namespace) -> int:
    root = ensure_workspace(args.workspace)
    json_print(
        {
            "status": "ready",
            "workspace": str(root),
            "created_or_verified": [
                "runtime.md",
                "inbox",
                "sources",
                "graph",
                "indexes",
                "projections",
                "overlays",
                "backups",
            ],
        }
    )
    return 0


def command_setup(args: argparse.Namespace) -> int:
    root = ensure_workspace(args.workspace)
    style = harness_style(args.harness)
    target = args.target or default_target_for(args.harness)
    code, message = update_adapter(root, target, approve=args.apply, remove=False, style=style)
    action = "applied" if args.apply else "preview"
    print(f"Workspace ready: {root}")
    print(f"Adapter {action} for {args.harness}: {target}")
    if not args.apply:
        print("Apply with the same command plus --apply.")
    if message:
        print(message)
    return code


def command_new(args: argparse.Namespace) -> int:
    root = require_workspace(args.workspace)
    relative, content = scaffold_record(args.kind, args.id, title=args.title, task=args.task)
    path = root / relative
    if path.exists() and not args.force:
        raise MarshmallowError(f"Already exists: {path} (use --force to overwrite)")
    atomic_write(path, content)
    remaining = [error for error in validate_workspace(root) if str(path) in error]
    json_print(
        {
            "status": "created",
            "kind": args.kind,
            "path": str(path),
            "next_steps": remaining
            or ["fill in the TODO placeholders, then run `doctor` to validate"],
        }
    )
    return 0


def command_doctor(args: argparse.Namespace) -> int:
    root = require_workspace(args.workspace)
    errors = validate_workspace(root)
    warnings = graph_quality_warnings(root)
    warnings.extend(runtime_guidance_warnings(root))

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
    skills = discover(args.home, args.project, args.additional or [], root)
    try:
        sources = source_cards(root)
        nodes = graph_nodes(root)
        indexes = index_pages(root)
        projection_pages = projections(root)
    except MarshmallowError:
        sources = {}
        nodes = {}
        indexes = {}
        projection_pages = {}
    report = {
        "workspace": str(root),
        "workspace_status": "ok" if not errors else "error",
        "errors": errors,
        "warnings": warnings,
        "runtime_exists": (root / "runtime.md").is_file(),
        "directories": {
            name: (root / name).is_dir()
            for name in ("inbox", "sources", "graph", "indexes", "projections", "overlays", "backups")
        },
        "counts": {
            "sources": len(sources),
            "graph_nodes": len(nodes),
            "indexes": len(indexes),
            "projections": len(projection_pages),
            "overlays": len([path for path in (root / "overlays").glob("*.md") if path.name != "README.md"]),
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
        print(f"Indexes: {report['counts']['indexes']}, projections: {report['counts']['projections']}")
        for name, info in harnesses.items():
            print(f"Adapter ({name}): {info['status']} ({info['target']})")
        print(f"Skills: {report['skills_found']} found, {report['recommended_skills']} recommended")
        print(f"Warnings: {len(warnings)}")
        for error in errors:
            print(f"ERROR: {error}")
        for warning in warnings:
            print(f"WARNING: {warning}")
    any_adapter_error = any(info.get("status") == "error" for info in harnesses.values())
    return 0 if not errors and not any_adapter_error else 1


def command_scan_skills(args: argparse.Namespace) -> int:
    json_print(discover(args.home, args.project, args.additional or [], args.workspace))
    return 0


def command_recall(args: argparse.Namespace) -> int:
    results = recall_context(args.workspace, args.query, limit=args.limit)
    if args.json:
        json_print({"query": args.query, "results": results})
        return 0
    if not results:
        print("No matching context found.")
        return 0
    for result in results:
        label = result["title"] or result["insight"] or result["task"] or result["id"]
        print(f"{result['score']:>3} {result['kind']} {result['id']} - {label}")
        print(f"    {result['path']}")
        if result["type"] or result["subjects"]:
            subjects = ", ".join(result["subjects"])
            metadata = ", ".join(item for item in (result["type"], subjects) if item)
            print(f"    {metadata}")
        if result["snippet"]:
            print(f"    {result['snippet']}")
        for citation in result.get("sources", []):
            print(f"    source: {citation['id']} ({citation['pointer'] or 'unresolved'})")
    return 0


def command_remember(args: argparse.Namespace) -> int:
    path, candidate_id = remember(args.workspace, args.note, why=args.why, origin=args.origin)
    json_print(
        {
            "status": "captured",
            "id": candidate_id,
            "path": str(path),
            "note": "Untrusted candidate in inbox. Nothing in the graph changed. "
            "Review with `pending`, then `promote` to make it source-backed.",
        }
    )
    return 0


def command_pending(args: argparse.Namespace) -> int:
    candidates = list_candidates(args.workspace, include_promoted=args.all)
    if args.json:
        json_print({"candidates": candidates})
        return 0
    if not candidates:
        print("No inbox candidates awaiting promotion.")
        return 0
    for candidate in candidates:
        print(f"{candidate['status']:>8} {candidate['id']} - {candidate['summary']}")
        print(f"         {candidate['path']}")
    return 0


def command_promote(args: argparse.Namespace) -> int:
    plan = promote(args.workspace, args.id, apply=args.apply)
    if args.json:
        json_print(plan)
        return 0
    if plan["status"] == "preview":
        print(f"Preview: would create source {plan['source_id']} at {plan['source_path']}")
        print(f"Next: {plan['next_step']}")
        print("Apply with the same command plus --apply.")
        return 0
    print(f"Promoted {plan['candidate_id']} -> source {plan['source_id']} ({plan['source_path']})")
    print(f"Next: {plan['next_step']}")
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

    setup = subparsers.add_parser("setup", help="Create the workspace and preview/apply a harness adapter.")
    add_workspace(setup)
    setup.add_argument(
        "--harness",
        choices=("claude", "codex", "cursor"),
        default="codex",
        help="Harness to connect. codex writes ~/.codex/AGENTS.md; cursor writes ./AGENTS.md.",
    )
    setup.add_argument("--target", type=Path, help="Override the adapter target file.")
    setup.add_argument("--apply", action="store_true", help="Write the adapter instead of printing only the preview.")
    setup.set_defaults(func=command_setup)

    new = subparsers.add_parser(
        "new",
        help="Scaffold a valid source, node, index, projection, or overlay skeleton.",
    )
    add_workspace(new)
    new.add_argument("kind", choices=SCAFFOLD_KINDS, help="What to scaffold.")
    new.add_argument("id", help="lowercase-hyphen-case id; also the filename stem.")
    new.add_argument("--title", default=None, help="Optional human title (defaults from the id).")
    new.add_argument("--task", default=None, help="For projections: the task this packet prepares for.")
    new.add_argument("--force", action="store_true", help="Overwrite if the file already exists.")
    new.set_defaults(func=command_new)

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

    recall = subparsers.add_parser("recall", help="Find source-backed context for a task, entity, or decision.")
    add_workspace(recall)
    recall.add_argument("query", help="Task, person, decision, or topic to find context for.")
    recall.add_argument("--json", action="store_true")
    recall.add_argument("--limit", type=int, default=10)
    recall.set_defaults(func=command_recall)

    remember_parser = subparsers.add_parser(
        "remember",
        help="Capture a note into the inbox as an untrusted candidate. Zero approval; the graph is untouched.",
    )
    add_workspace(remember_parser)
    remember_parser.add_argument("note", help="The thing worth keeping (a fact, decision, correction, or observation).")
    remember_parser.add_argument("--why", help="Optional reason this matters.")
    remember_parser.add_argument("--origin", help="Optional provenance: a file path, URL, or session context.")
    remember_parser.set_defaults(func=command_remember)

    pending = subparsers.add_parser("pending", help="List inbox candidates awaiting promotion.")
    add_workspace(pending)
    pending.add_argument("--all", action="store_true", help="Include already-promoted candidates.")
    pending.add_argument("--json", action="store_true")
    pending.set_defaults(func=command_pending)

    promote_parser = subparsers.add_parser(
        "promote",
        help="Promote an inbox candidate into a source card (the trust gate). Preview unless --apply.",
    )
    add_workspace(promote_parser)
    promote_parser.add_argument("id", help="Candidate id from `pending`.")
    promote_parser.add_argument("--apply", action="store_true", help="Write the source card and mark the candidate promoted.")
    promote_parser.add_argument("--json", action="store_true")
    promote_parser.set_defaults(func=command_promote)

    adapter = subparsers.add_parser("adapter", help="Preview, apply, or remove a runtime adapter.")
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
