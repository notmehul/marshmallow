#!/usr/bin/env python3
"""The capture -> promote half of the Marshmallow loop.

Capture is zero-resistance: ``remember`` drops a note into ``inbox/`` with no
approval, because the inbox is untrusted by construction. Durability is earned:
``promote`` turns a reviewed candidate into a source card, which is the
provenance anchor a graph node then cites. The trust gate lives at promotion,
not capture, so any model can store freely without ever touching the graph.

This module only handles the deterministic file plumbing. The synthesis
judgment -- what insight a candidate becomes -- stays with the agent or person,
who writes the graph node (`new node`) that cites the promoted source.
"""

from __future__ import annotations

import secrets
from pathlib import Path
from typing import Any

from markdown_graph import ID_PATTERN, frontmatter_scalar, parse_frontmatter, slugify
from marshmallow_workspace import (
    MarshmallowError,
    atomic_write,
    ensure_workspace,
    iso_timestamp,
    require_workspace,
    timestamp,
)

SLUG_LIMIT = 48
HEADING_LIMIT = 80


def _first_line(body: str) -> str:
    for line in body.splitlines():
        stripped = line.strip().lstrip("# ").strip()
        if stripped:
            return stripped[:HEADING_LIMIT]
    return ""


def _candidate_id(heading: str) -> str:
    slug = slugify(heading)[:SLUG_LIMIT].strip("-") or "note"
    return f"candidate-{timestamp().lower()}-{slug}-{secrets.token_hex(4)}"


def remember(
    root: Path,
    note: str,
    *,
    why: str | None = None,
    origin: str | None = None,
) -> tuple[Path, str]:
    """Capture a note into the inbox as an untrusted candidate. No approval."""

    note = note.strip()
    if not note:
        raise MarshmallowError("remember needs a non-empty note")
    root = ensure_workspace(root)
    heading = _first_line(note) or "note"
    candidate_id = _candidate_id(heading)
    path = root / "inbox" / f"{candidate_id}.md"
    if path.exists():
        raise MarshmallowError(f"Candidate already exists: {path}")

    origin_line = f"origin: {frontmatter_scalar(origin.strip())}\n" if origin and origin.strip() else ""
    body = note
    if why and why.strip():
        body += f"\n\n**Why:** {why.strip()}"
    card = (
        "---\n"
        f"id: {candidate_id}\n"
        f"captured: {iso_timestamp()}\n"
        "status: pending\n"
        f"{origin_line}"
        "---\n\n"
        f"# {heading}\n\n"
        f"{body}\n"
    )
    atomic_write(path, card)
    return path, candidate_id


def _read_candidate(path: Path) -> tuple[dict[str, Any], str]:
    """Parse an inbox file, tolerating free-form notes with no frontmatter."""

    try:
        frontmatter, body = parse_frontmatter(path)
    except MarshmallowError:
        return {}, path.read_text(encoding="utf-8")
    return frontmatter, body


def list_candidates(root: Path, *, include_promoted: bool = False) -> list[dict[str, Any]]:
    """List inbox candidates awaiting promotion (the synthesis work queue)."""

    root = require_workspace(root)
    candidates: list[dict[str, Any]] = []
    for path in sorted((root / "inbox").glob("*.md")):
        if path.name == "README.md":
            continue
        frontmatter, body = _read_candidate(path)
        status = str(frontmatter.get("status") or "pending")
        if status == "promoted" and not include_promoted:
            continue
        candidates.append(
            {
                "id": str(frontmatter.get("id") or path.stem),
                "status": status,
                "captured": str(frontmatter.get("captured", "")),
                "origin": str(frontmatter.get("origin", "")),
                "summary": _first_line(body) or str(path.stem),
                "path": str(path),
            }
        )
    return candidates


def _find_candidate(root: Path, candidate_id: str) -> tuple[Path, dict[str, Any], str]:
    for path in sorted((root / "inbox").glob("*.md")):
        if path.name == "README.md":
            continue
        frontmatter, body = _read_candidate(path)
        if str(frontmatter.get("id") or path.stem) == candidate_id:
            frontmatter.setdefault("id", path.stem)
            return path, frontmatter, body
    raise MarshmallowError(f"Inbox candidate not found: {candidate_id}")


def _mark_promoted(path: Path, frontmatter: dict[str, Any], body: str, source_id: str) -> None:
    fields = {
        "id": str(frontmatter.get("id") or path.stem),
        "captured": str(frontmatter.get("captured", "")),
        "status": "promoted",
        "promoted_to": source_id,
        "origin": str(frontmatter.get("origin", "")),
    }
    lines = ["---"]
    lines += [f"{key}: {frontmatter_scalar(value)}" for key, value in fields.items() if value]
    lines.append("---")
    atomic_write(path, "\n".join(lines) + "\n\n" + body.strip() + "\n")


def promote(root: Path, candidate_id: str, *, apply: bool = False) -> dict[str, Any]:
    """Promote an inbox candidate into a source card (the trust gate).

    Preview by default; ``apply`` writes the source card and marks the candidate
    promoted. Promotion creates only the *source* -- the agent or person then
    authors the graph node that cites it, keeping synthesis judgment human.
    """

    root = require_workspace(root)
    path, frontmatter, body = _find_candidate(root, candidate_id)
    if str(frontmatter.get("status") or "pending") == "promoted":
        raise MarshmallowError(f"Candidate already promoted: {candidate_id}")

    source_id = candidate_id if ID_PATTERN.match(candidate_id) else slugify(candidate_id)
    source_path = root / "sources" / f"{source_id}.md"
    if source_path.exists():
        raise MarshmallowError(f"Source already exists: {source_path}")

    origin = str(frontmatter.get("origin", "")).strip()
    pointer = origin or f"inbox-candidate:{candidate_id}"
    captured = str(frontmatter.get("captured", "")).strip() or iso_timestamp()
    summary = _first_line(body) or candidate_id
    source_content = (
        "---\n"
        f"id: {source_id}\n"
        f"pointer: {frontmatter_scalar(pointer)}\n"
        f"captured: {frontmatter_scalar(captured)}\n"
        f"summary: {frontmatter_scalar(summary)}\n"
        "labels: [inbox-promoted]\n"
        "---\n\n"
        f"# {summary}\n\n"
        f"{body.strip()}\n"
    )

    plan: dict[str, Any] = {
        "candidate_id": candidate_id,
        "source_id": source_id,
        "source_path": str(source_path),
        "next_step": (
            f"write a graph node that cites `{source_id}`: "
            f"`marshmallow.py new node <id>`, then set source_ids: [{source_id}]"
        ),
    }
    if not apply:
        plan["status"] = "preview"
        plan["preview"] = source_content
        return plan

    atomic_write(source_path, source_content)
    _mark_promoted(path, frontmatter, body, source_id)
    plan["status"] = "promoted"
    return plan
