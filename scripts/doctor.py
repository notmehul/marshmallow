#!/usr/bin/env python3
"""Report local Marshmallow installation health without mutating files."""

from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Any

from harness_adapter import END_MARKER, START_MARKER, default_claude_md
from markdown_graph import validate_workspace
from marshmallow_workspace import MarshmallowError, default_workspace, read_workspace
from skill_scanner import discover


def file_count(root: Path, relative: str, pattern: str = "*.md", exclude: set[str] | None = None) -> int:
    path = root / relative
    if not path.exists():
        return 0
    excluded = exclude or set()
    return len([item for item in path.glob(pattern) if item.name not in excluded])


def claude_version() -> str | None:
    if not shutil.which("claude"):
        return None
    result = subprocess.run(
        ["claude", "--version"],
        check=False,
        text=True,
        capture_output=True,
    )
    version = (result.stdout or result.stderr).strip()
    return version or None


def adapter_status(target: Path, workspace_root: Path) -> dict[str, Any]:
    if not target.exists():
        return {"status": "missing", "target": str(target)}
    text = target.read_text(encoding="utf-8")
    starts = text.count(START_MARKER)
    ends = text.count(END_MARKER)
    if starts == 0 and ends == 0:
        return {"status": "absent", "target": str(target)}
    if starts != 1 or ends != 1 or text.index(START_MARKER) > text.index(END_MARKER):
        return {"status": "malformed", "target": str(target), "start_markers": starts, "end_markers": ends}
    expected_runtime = str((workspace_root / "runtime.md").resolve())
    status = "installed" if expected_runtime in text else "installed-different-workspace"
    return {"status": status, "target": str(target), "runtime": expected_runtime}


def read_workspace_safely(root: Path) -> tuple[dict[str, Any] | None, list[str]]:
    if not (root / "workspace.json").exists():
        return None, [f"Workspace not initialized: {root / 'workspace.json'}"]
    try:
        return read_workspace(root), []
    except MarshmallowError as error:
        return None, [str(error)]


def doctor_report(workspace_root: Path, claude_md: Path, home: Path, project: Path) -> dict[str, Any]:
    workspace_root = workspace_root.expanduser()
    workspace, workspace_read_errors = read_workspace_safely(workspace_root)
    validation_errors = validate_workspace(workspace_root) if workspace else workspace_read_errors
    skills = discover(home.expanduser(), project.resolve(), [])
    recommended_skills = [skill for skill in skills if skill["recommended"]]
    backup_records = workspace.get("backup_records", []) if workspace else []
    adapter_records = workspace.get("adapter_records", []) if workspace else []
    return {
        "workspace": str(workspace_root),
        "workspace_status": "ok" if not validation_errors else "error",
        "workspace_errors": validation_errors,
        "runtime_exists": (workspace_root / "runtime.md").exists(),
        "graph_nodes": file_count(workspace_root, "graph"),
        "source_cards": file_count(workspace_root, "sources"),
        "projection_files": file_count(workspace_root, "projections"),
        "inbox_candidates": file_count(workspace_root, "inbox", exclude={"README.md"}),
        "overlays": file_count(workspace_root, "overlays"),
        "skills_found": len(skills),
        "recommended_skills": len(recommended_skills),
        "writable_recommended_skills": len([skill for skill in recommended_skills if skill["writable"]]),
        "tuned_skills": len(workspace.get("tuned_skills", {})) if workspace else 0,
        "skill_backups": len(backup_records),
        "adapter_records": len(adapter_records),
        "adapter": adapter_status(claude_md.expanduser(), workspace_root),
        "claude_version": claude_version(),
        "python_version": sys.version.split()[0],
    }


def render_human(report: dict[str, Any]) -> str:
    lines = [
        "Marshmallow Doctor",
        "",
        f"Workspace: {report['workspace_status']} ({report['workspace']})",
        f"Runtime: {'present' if report['runtime_exists'] else 'missing'}",
        f"Graph nodes: {report['graph_nodes']}",
        f"Source cards: {report['source_cards']}",
        f"Projection files: {report['projection_files']}",
        f"Inbox candidates: {report['inbox_candidates']}",
        f"Overlays: {report['overlays']}",
        f"Skills found: {report['skills_found']}",
        f"Recommended skills: {report['recommended_skills']}",
        f"Writable recommended skills: {report['writable_recommended_skills']}",
        f"Tuned skills: {report['tuned_skills']}",
        f"Adapter: {report['adapter']['status']} ({report['adapter']['target']})",
        f"Skill backups: {report['skill_backups']}",
        f"Adapter records: {report['adapter_records']}",
        f"Claude Code: {report['claude_version'] or 'not found'}",
        f"Python: {report['python_version']}",
    ]
    if report["workspace_errors"]:
        lines.extend(["", "Workspace Errors:"])
        lines.extend(f"- {error}" for error in report["workspace_errors"])
    return "\n".join(lines) + "\n"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--workspace", type=Path, default=default_workspace())
    parser.add_argument("--claude-md", type=Path, default=default_claude_md())
    parser.add_argument("--home", type=Path, default=Path.home())
    parser.add_argument("--project", type=Path, default=Path.cwd())
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()
    report = doctor_report(args.workspace, args.claude_md, args.home, args.project)
    if args.json:
        print(json.dumps(report, indent=2, sort_keys=True))
    else:
        print(render_human(report), end="")
    return 1 if report["workspace_status"] != "ok" or report["adapter"]["status"] == "malformed" else 0


if __name__ == "__main__":
    raise SystemExit(main())
