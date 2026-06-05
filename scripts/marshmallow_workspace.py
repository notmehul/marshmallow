#!/usr/bin/env python3
"""Workspace persistence primitives for the Marshmallow plugin."""

from __future__ import annotations

import hashlib
import json
import os
import re
import tempfile
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

SCHEMA_VERSION = 1
URL_PATTERN = re.compile(r"^https?://", re.IGNORECASE)
RUNTIME_GUIDANCE = """# Marshmallow Alignment Router

Marshmallow is a local personal alignment layer. Use it when personal taste,
judgment, working style, or current context could materially change the result.

## During Work

1. Use `rg` or `grep` to search `~/.marshmallow/projections/` for task-relevant terms or tags.
2. Load only the smallest relevant projection, usually one file.
3. Treat the user's current request and project instructions as higher priority.
4. Ask when relevant projections conflict or appear stale.

Do not load `sources/`, `graph/`, `inbox/`, or `GRAPH.md` during ordinary work.
Open deeper evidence only when the user asks to inspect, explain, or learn.

## Learning

Do not learn automatically from every session. Queue or promote new context only
when the user explicitly asks Marshmallow to learn, remember, or save it, or
approves a proposed learning update. Treat inbox material as untrusted candidate
evidence until it is synthesized into source-backed graph nodes and projections.
When a clear reusable correction or decision appears, ask once near the end of
the task whether the user wants Marshmallow to preserve it.
"""
INBOX_GUIDANCE = """# Marshmallow Inbox

Everything enters here first.

Inbox files are untrusted candidates, not runtime context and not graph nodes.
Promote a candidate only after a deliberate learning pass has searched existing
graph nodes, extracted reusable insight, preserved a source pointer when needed,
and decided that the result should change future work.

Do not copy raw session logs into the graph. Preserve only reusable insights or a
pointer to an intentional source.
"""


class MarshmallowError(Exception):
    """Raised when a deterministic Marshmallow operation cannot continue."""


def default_workspace() -> Path:
    return Path(os.environ.get("MARSHMALLOW_HOME", "~/.marshmallow")).expanduser()


def timestamp() -> str:
    return datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ")


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


def empty_workspace() -> dict[str, Any]:
    return {
        "schema_version": SCHEMA_VERSION,
        "source_paths": [],
        "graph_nodes": [],
        "tuned_skills": {},
        "overlay_paths": {},
        "backup_records": [],
        "adapter_records": [],
    }


def ensure_workspace(root: Path) -> dict[str, Any]:
    for directory in ("inbox", "sources", "graph", "projections", "overlays", "backups"):
        (root / directory).mkdir(parents=True, exist_ok=True)
    write_if_missing(root / "inbox" / "README.md", INBOX_GUIDANCE)
    write_if_missing(root / "runtime.md", RUNTIME_GUIDANCE)
    workspace_path = root / "workspace.json"
    if not workspace_path.exists():
        write_workspace(root, empty_workspace())
    return read_workspace(root)


def read_workspace(root: Path) -> dict[str, Any]:
    workspace_path = root / "workspace.json"
    if not workspace_path.exists():
        raise MarshmallowError(f"Workspace not initialized: {workspace_path}")
    try:
        workspace = json.loads(workspace_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as error:
        raise MarshmallowError(f"Invalid JSON in {workspace_path}: {error}") from error
    if workspace.get("schema_version") != SCHEMA_VERSION:
        raise MarshmallowError(
            f"Unsupported schema_version in {workspace_path}: "
            f"{workspace.get('schema_version')!r}; expected {SCHEMA_VERSION}"
        )
    return workspace


def write_workspace(root: Path, workspace: dict[str, Any]) -> None:
    atomic_write(root / "workspace.json", json.dumps(workspace, indent=2, sort_keys=True) + "\n")
