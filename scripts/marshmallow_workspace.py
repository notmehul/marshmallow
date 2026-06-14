#!/usr/bin/env python3
"""Workspace primitives for the Marshmallow plugin.

Marshmallow intentionally avoids a central state file. The workspace is a
small collection of plain files; deterministic tools mutate those files and
write rollback records beside their backups.
"""

from __future__ import annotations

import hashlib
import json
import os
import re
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

URL_PATTERN = re.compile(r"^https?://", re.IGNORECASE)
UTC = timezone.utc

WORKSPACE_DIRS = ("inbox", "sources", "graph", "indexes", "projections", "overlays", "backups")

RUNTIME_GUIDANCE = """# Marshmallow Alignment Router

Marshmallow is a local source-backed recall layer. Use it when people, projects,
decisions, working rules, or current context could materially change the result.

## During Work

1. Run `marshmallow.py recall "<task/person/decision>"` when the CLI is
   available, or check `~/.marshmallow/indexes/` first for compact navigation
   pages relevant to the task.
2. Use `rg` or `grep` to search `~/.marshmallow/graph/` only after recall or
   indexes. Load the smallest relevant graph nodes, usually three to seven files.
3. Use or create a focused `~/.marshmallow/projections/` recall packet when the
   task needs a reusable brief. Treat recall packets as runtime aids, not source
   truth.
4. Treat the user's current request, project instructions, and safety rules as
   higher priority than Marshmallow guidance.
5. Ask when graph nodes conflict, seem stale, or would change a user-visible
   decision.

Do not crawl the whole graph by default. Do not load `sources/` or `inbox/`
during ordinary work. Do not send, post, queue, or automate on Marshmallow's
behalf. Open deeper evidence only when the user asks to inspect, explain, or
learn.

## Learning

Do not learn automatically from every session. Preserve new context only when
the user explicitly asks Marshmallow to learn, remember, save, tune, or approve
a proposed learning update. Treat inbox material as untrusted candidate evidence
until it is synthesized into source-backed graph nodes.
"""

INBOX_GUIDANCE = """# Marshmallow Inbox

Everything enters here first.

Inbox files are untrusted candidates, not runtime context and not graph nodes.
Promote a candidate only after a deliberate learning pass has searched existing
graph nodes, extracted reusable insight, preserved a source pointer when needed,
and decided that the result should change future work.

Do not copy raw session logs into the graph. Preserve only reusable insights or
a pointer to an intentional source.
"""

INDEX_GUIDANCE = """# Marshmallow Indexes

Indexes are agent-written Markdown navigation pages. They summarize what to
look at first so future agents do not crawl the whole graph.

Indexes are runtime aids, not source truth. Durable knowledge stays in
`graph/`, backed by `sources/`.
"""

PROJECTION_GUIDANCE = """# Marshmallow Projections

Projections are task-shaped recall packets written by agents for a specific job,
workflow, meeting, or handoff.

Use projections to collect the few graph nodes, open loops, constraints, and
source trails that matter now. Projections are runtime aids, not durable source
truth.
"""


class MarshmallowError(Exception):
    """Raised when a deterministic Marshmallow operation cannot continue."""


def default_workspace() -> Path:
    return Path(os.environ.get("MARSHMALLOW_HOME", "~/.marshmallow")).expanduser()


def timestamp() -> str:
    return datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ")


def iso_timestamp() -> str:
    return datetime.now(UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def sha256_bytes(content: bytes) -> str:
    return hashlib.sha256(content).hexdigest()


def sha256_file(path: Path) -> str:
    return sha256_bytes(path.read_bytes())


def atomic_write(path: Path, content: str | bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    mode = "wb" if isinstance(content, bytes) else "w"
    kwargs: dict[str, Any] = {} if isinstance(content, bytes) else {"encoding": "utf-8"}
    with tempfile.NamedTemporaryFile(mode=mode, dir=path.parent, delete=False, **kwargs) as handle:
        handle.write(content)
        temp_path = Path(handle.name)
    os.replace(temp_path, path)


def write_if_missing(path: Path, content: str) -> None:
    if not path.exists():
        atomic_write(path, content)


def require_workspace(root: Path) -> Path:
    root = root.expanduser()
    if not root.exists():
        raise MarshmallowError(f"Workspace not found: {root}. Run init first.")
    return root


def ensure_workspace(root: Path) -> Path:
    root = root.expanduser()
    for directory in WORKSPACE_DIRS:
        (root / directory).mkdir(parents=True, exist_ok=True)
    write_if_missing(root / "inbox" / "README.md", INBOX_GUIDANCE)
    write_if_missing(root / "indexes" / "README.md", INDEX_GUIDANCE)
    write_if_missing(root / "projections" / "README.md", PROJECTION_GUIDANCE)
    write_if_missing(root / "runtime.md", RUNTIME_GUIDANCE)
    return root


def write_record(path: Path, record: dict[str, Any]) -> None:
    atomic_write(path, json.dumps(record, indent=2, sort_keys=True) + "\n")


def source_status(pointer: str) -> dict[str, str | bool]:
    """Return a small onboarding hint for a source pointer."""

    if URL_PATTERN.match(pointer):
        return {
            "accepted": True,
            "message": "URL accepted. If the host agent cannot fetch it, paste a short excerpt into inbox.",
        }
    path = Path(pointer).expanduser()
    if path.exists():
        return {"accepted": True, "message": f"Local source found: {path}"}
    return {
        "accepted": False,
        "message": "Source not found. Use a real path/URL or paste an excerpt into inbox with a source pointer.",
    }
