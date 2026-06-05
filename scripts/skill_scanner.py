#!/usr/bin/env python3
"""Discover Claude Code skills that may benefit from personal alignment."""

from __future__ import annotations

import re
from pathlib import Path

from markdown_graph import parse_frontmatter
from marshmallow_workspace import MarshmallowError
from skill_overlay import is_writable, normalize_skill_file

DETERMINISTIC_KEYWORDS = {
    "extract",
    "format",
    "lint",
    "merge",
    "migration",
    "pdf",
    "security",
    "tax",
    "validate",
}
JUDGMENT_KEYWORDS = {
    "architecture",
    "brainstorm",
    "build",
    "code",
    "design",
    "draft",
    "edit",
    "frontend",
    "plan",
    "product",
    "review",
    "strategy",
    "ui",
    "ux",
    "write",
}


def scope_for(path: Path, home: Path, project: Path) -> str:
    try:
        path.relative_to(home / ".claude" / "skills")
        return "personal"
    except ValueError:
        pass
    try:
        path.relative_to(project / ".claude" / "skills")
        return "project"
    except ValueError:
        return "additional"


def candidate_paths(root: Path) -> list[Path]:
    if root.name == "SKILL.md":
        return [root]
    direct = root / "SKILL.md"
    if direct.exists():
        return [direct]
    return sorted(root.glob("*/SKILL.md"))


def is_excluded(path: Path) -> bool:
    parts = set(path.parts)
    if "plugins" in parts and "cache" in parts:
        return True
    return path.parent.name in {"marshmallow", "start"}


def recommendation(path: Path) -> tuple[bool, str]:
    text = path.read_text(encoding="utf-8").lower()
    try:
        frontmatter, _ = parse_frontmatter(path)
        description = str(frontmatter.get("description", "")).lower()
    except MarshmallowError:
        description = ""
    haystack = f"{path.parent.name.lower()} {description} {text}"
    judgment_hits = keyword_hits(haystack, JUDGMENT_KEYWORDS)
    deterministic_hits = keyword_hits(haystack, DETERMINISTIC_KEYWORDS)
    if deterministic_hits:
        return False, f"Likely deterministic workflow: {', '.join(deterministic_hits[:5])}"
    if judgment_hits:
        return True, f"Judgment-sensitive keywords: {', '.join(judgment_hits[:5])}"
    return False, "No clear judgment-sensitive behavior detected; offer only if the user asks."


def keyword_hits(text: str, keywords: set[str]) -> list[str]:
    return sorted(
        keyword
        for keyword in keywords
        if re.search(rf"\b{re.escape(keyword)}(?:s|ed|ing)?\b", text)
    )


def discover(home: Path, project: Path, additional: list[Path]) -> list[dict[str, str | bool]]:
    roots = [home / ".claude" / "skills", project / ".claude" / "skills", *additional]
    seen: set[Path] = set()
    skills: list[dict[str, str | bool]] = []
    for root in roots:
        if not root.expanduser().exists():
            continue
        for path in candidate_paths(root.expanduser()):
            resolved = normalize_skill_file(path).resolve()
            if resolved in seen or is_excluded(resolved):
                continue
            seen.add(resolved)
            recommended, reason = recommendation(resolved)
            skills.append(
                {
                    "name": resolved.parent.name,
                    "path": str(resolved),
                    "scope": scope_for(resolved, home, project),
                    "writable": is_writable(resolved),
                    "recommended": recommended,
                    "reason": reason,
                }
            )
    return sorted(skills, key=lambda item: (str(item["scope"]), str(item["name"])))
