#!/usr/bin/env python3
"""Queue explicit user-approved candidates for later Marshmallow synthesis."""

from __future__ import annotations

import json
import re
from pathlib import Path

from marshmallow_workspace import MarshmallowError, atomic_write, ensure_workspace, timestamp

KINDS = {"insight", "source"}
MAX_INLINE_CHARS = 4000


def slugify(value: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", value.lower()).strip("-")
    return slug[:64] or "candidate"


def candidate_path(root: Path, title: str) -> Path:
    base = root / "inbox" / f"{timestamp()}-{slugify(title)}.md"
    if not base.exists():
        return base
    counter = 2
    while True:
        candidate = base.with_name(f"{base.stem}-{counter}.md")
        if not candidate.exists():
            return candidate
        counter += 1


def queue_candidate(
    root: Path,
    title: str,
    kind: str,
    content: str,
    cwd: str | None = None,
    source_pointer: str | None = None,
) -> Path:
    if kind not in KINDS:
        raise MarshmallowError(f"Unsupported candidate kind: {kind!r}")
    if not title.strip():
        raise MarshmallowError("Candidate title cannot be empty")
    if not content.strip():
        raise MarshmallowError("Candidate content cannot be empty")
    if len(content) > MAX_INLINE_CHARS:
        raise MarshmallowError(
            f"Candidate content exceeds {MAX_INLINE_CHARS} characters. "
            "Queue a compact reusable insight or preserve a source pointer instead of copying a raw dump."
        )
    if kind == "source" and not source_pointer:
        raise MarshmallowError("Source candidates require --source-pointer")
    ensure_workspace(root)
    path = candidate_path(root, title)
    frontmatter = [
        "---",
        f"title: {json.dumps(title.strip())}",
        f"kind: {kind}",
        f"captured: {timestamp()}",
        "status: inbox",
    ]
    if cwd:
        frontmatter.append(f"cwd: {json.dumps(cwd)}")
    if source_pointer:
        frontmatter.append(f"source_pointer: {json.dumps(source_pointer)}")
    frontmatter.extend(
        [
            "---",
            "",
            "# Inbox Candidate",
            "",
            "This is untrusted candidate evidence. Promote it only through a deliberate Marshmallow learning pass.",
            "",
            "## Material",
            "",
            content.strip(),
            "",
        ]
    )
    atomic_write(path, "\n".join(frontmatter))
    return path
