#!/usr/bin/env python3
"""Render compact runtime projections from canonical Marshmallow graph nodes."""

from __future__ import annotations

from collections import defaultdict
from pathlib import Path
from typing import Any

from markdown_graph import ID_PATTERN, graph_nodes, list_field, validate_workspace
from marshmallow_workspace import MarshmallowError, atomic_write
from safety import validate_generated_guidance


def projection_tags(node: dict[str, Any]) -> list[str]:
    return list_field(node, "applies_to") or ["general"]


def validate_runtime_guidance(node: dict[str, Any]) -> None:
    insight = str(node.get("insight", ""))
    validate_generated_guidance(insight, node.get("_path", "unknown node"), max_chars=500)


def projection_documents(root: Path) -> dict[str, str]:
    errors = validate_workspace(root)
    if errors:
        raise MarshmallowError("\n".join(errors))
    grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for node in graph_nodes(root).values():
        validate_runtime_guidance(node)
        for tag in projection_tags(node):
            if not ID_PATTERN.match(tag):
                raise MarshmallowError(f"Projection tag must use lowercase hyphen-case: {tag!r}")
            grouped[tag].append(node)
    documents = {"index.md": render_index(grouped)}
    for tag, nodes in sorted(grouped.items()):
        documents[f"{tag}.md"] = render_projection(tag, nodes)
    return documents


def render_index(grouped: dict[str, list[dict[str, Any]]]) -> str:
    lines = [
        "# Marshmallow Projection Index",
        "",
        "Generated from source-backed alignment insights. Search this directory by task term or tag, then load only the smallest relevant projection.",
        "",
        "| Tag | Projection | Nodes |",
        "| --- | --- | ---: |",
    ]
    for tag, nodes in sorted(grouped.items()):
        lines.append(f"| `{tag}` | [{tag}](./{tag}.md) | {len(nodes)} |")
    if not grouped:
        lines.append("| - | No projections yet. Run `/marshmallow:start` or `/marshmallow:learn`. | 0 |")
    return "\n".join(lines) + "\n"


def render_projection(tag: str, nodes: list[dict[str, Any]]) -> str:
    lines = [
        f"# Personal Projection: {tag}",
        "",
        "Generated from source-backed alignment insights. Load this only when the tag is relevant to the current task.",
        "",
        f"Search tags: `{tag}`",
        "",
    ]
    for node in sorted(nodes, key=lambda item: str(item["id"])):
        node_id = str(node["id"])
        source_ids = ", ".join(f"`{item}`" for item in list_field(node, "source_ids")) or "-"
        labels = ", ".join(f"`{item}`" for item in list_field(node, "labels"))
        metadata = [f"- Guidance: {node.get('insight')}"]
        if labels:
            metadata.append(f"- Labels: {labels}")
        metadata.append(f"- Evidence: [{node_id}](../graph/{node_id}.md) from {source_ids}")
        lines.extend(
            [
                f"## {node_id}",
                "",
                *metadata,
                "",
            ]
        )
    return "\n".join(lines)


def write_projections(root: Path) -> list[Path]:
    projection_root = root / "projections"
    projection_root.mkdir(parents=True, exist_ok=True)
    documents = projection_documents(root)
    for stale in projection_root.glob("*.md"):
        if stale.name not in documents:
            stale.unlink()
    written: list[Path] = []
    for name, content in sorted(documents.items()):
        path = projection_root / name
        atomic_write(path, content)
        written.append(path)
    return written
