#!/usr/bin/env python3
"""Complete, read-only access to Marshmallow runtime records."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from markdown_graph import (
    graph_nodes,
    index_pages,
    keyed_hash_field,
    list_field,
    parse_frontmatter,
    projections,
    readable_source_cards,
)
from marshmallow_workspace import MarshmallowError, require_workspace, sha256_file

KIND_ALIASES = {
    "graph": "graph",
    "source": "source",
    "index": "index",
    "projection": "recall-packet",
    "recall-packet": "recall-packet",
}


def _records_by_kind(root: Path) -> dict[str, dict[str, dict[str, Any]]]:
    return {
        "graph": graph_nodes(root),
        "source": readable_source_cards(root),
        "index": index_pages(root),
        "recall-packet": projections(root),
    }


def _resolve_sources(
    frontmatter: dict[str, Any],
    sources: dict[str, dict[str, Any]],
) -> list[dict[str, str]]:
    resolved: list[dict[str, str]] = []
    for source_id in list_field(frontmatter, "source_ids"):
        source = sources.get(source_id, {})
        resolved.append(
            {
                "id": source_id,
                "pointer": str(source.get("pointer", "")),
                "kind": str(source.get("kind", "")),
                "path": str(source.get("_path", "")),
            }
        )
    return resolved


def receipt_target_hashes(receipt: dict[str, Any]) -> dict[str, str]:
    """Parse ``node-id=sha256`` values from a managed-update receipt."""

    return keyed_hash_field(receipt, "target_hashes")


def managed_lineage_status(
    root: Path,
    node_id: str,
    frontmatter: dict[str, Any],
    *,
    sources: dict[str, dict[str, Any]] | None = None,
) -> dict[str, str]:
    if str(frontmatter.get("managed", "")).strip() != "true":
        return {"status": "not-managed", "revision_source_id": ""}

    revision_id = str(frontmatter.get("revision_source_id", "")).strip()
    if not revision_id:
        return {"status": "legacy", "revision_source_id": ""}

    sources = sources or readable_source_cards(root)
    receipt = sources.get(revision_id)
    if not receipt or str(receipt.get("kind", "")) != "managed-update":
        return {"status": "broken", "revision_source_id": revision_id}
    if node_id not in list_field(receipt, "target_ids"):
        return {"status": "broken", "revision_source_id": revision_id}

    expected_hash = receipt_target_hashes(receipt).get(node_id, "")
    path = Path(str(frontmatter.get("_path", "")))
    if not expected_hash or not path.is_file():
        return {"status": "broken", "revision_source_id": revision_id}
    if sha256_file(path) != expected_hash:
        return {"status": "drifted", "revision_source_id": revision_id}
    return {"status": "current", "revision_source_id": revision_id}


def get_record(root: Path, record_id: str, *, kind: str | None = None) -> dict[str, Any]:
    """Return one complete runtime record with citations and a content hash."""

    root = require_workspace(root)
    records_by_kind = _records_by_kind(root)
    if kind:
        normalized_kind = KIND_ALIASES.get(kind)
        if not normalized_kind:
            choices = ", ".join(sorted(KIND_ALIASES))
            raise MarshmallowError(f"Unknown record kind {kind!r}; choose one of {choices}")
        candidates = [(normalized_kind, records_by_kind[normalized_kind].get(record_id))]
    else:
        candidates = [(name, records.get(record_id)) for name, records in records_by_kind.items()]

    matches = [(name, item) for name, item in candidates if item is not None]
    if not matches:
        raise MarshmallowError(f"Record not found: {record_id}")
    if len(matches) > 1:
        kinds = ", ".join(name for name, _ in matches)
        raise MarshmallowError(f"Record id {record_id!r} is ambiguous across: {kinds}; pass --kind")

    record_kind, frontmatter = matches[0]
    path = Path(str(frontmatter["_path"]))
    _, body = parse_frontmatter(path)
    sources = readable_source_cards(root)
    public_frontmatter = {key: value for key, value in frontmatter.items() if not key.startswith("_")}
    revision_id = str(frontmatter.get("revision_source_id", "")).strip()
    revision = sources.get(revision_id, {}) if revision_id else {}
    lineage = (
        managed_lineage_status(root, record_id, frontmatter, sources=sources)
        if record_kind == "graph"
        else {"status": "not-managed", "revision_source_id": ""}
    )
    return {
        "id": record_id,
        "kind": record_kind,
        "path": str(path),
        "content_hash": sha256_file(path),
        "frontmatter": public_frontmatter,
        "body": body,
        "related_nodes": list_field(frontmatter, "related_nodes"),
        "graph_ids": list_field(frontmatter, "graph_ids"),
        "sources": _resolve_sources(frontmatter, sources) if record_kind == "graph" else [],
        "revision_source": (
            {
                "id": revision_id,
                "pointer": str(revision.get("pointer", "")),
                "kind": str(revision.get("kind", "")),
                "path": str(revision.get("_path", "")),
            }
            if revision_id
            else None
        ),
        "lineage": lineage,
    }
