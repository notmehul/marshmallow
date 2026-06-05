#!/usr/bin/env python3
"""Markdown graph parsing, validation, indexing, and rendering."""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any

from marshmallow_workspace import MarshmallowError, read_workspace, write_workspace

REQUIRED_NODE_FIELDS = {"id", "insight", "source_ids"}
ID_PATTERN = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")


def parse_frontmatter(path: Path) -> tuple[dict[str, Any], str]:
    text = path.read_text(encoding="utf-8")
    if not text.startswith("---\n"):
        raise MarshmallowError(f"Missing YAML frontmatter: {path}")
    closing = text.find("\n---\n", 4)
    if closing == -1:
        raise MarshmallowError(f"Unclosed YAML frontmatter: {path}")
    return parse_simple_yaml(text[4:closing], path), text[closing + 5 :]


def parse_simple_yaml(text: str, path: Path) -> dict[str, Any]:
    result: dict[str, Any] = {}
    active_list: str | None = None
    for raw_line in text.splitlines():
        if not raw_line.strip() or raw_line.lstrip().startswith("#"):
            continue
        if raw_line.startswith("  - ") and active_list:
            result[active_list].append(unquote(raw_line[4:].strip()))
            continue
        if ":" not in raw_line:
            raise MarshmallowError(f"Unsupported frontmatter line in {path}: {raw_line!r}")
        key, raw_value = raw_line.split(":", 1)
        key = key.strip()
        raw_value = raw_value.strip()
        active_list = None
        if not raw_value:
            result[key] = []
            active_list = key
        elif raw_value.startswith("[") and raw_value.endswith("]"):
            result[key] = parse_inline_list(raw_value[1:-1])
        else:
            result[key] = unquote(raw_value)
    return result


def unquote(value: str) -> str:
    if len(value) >= 2 and value[0] == value[-1] and value[0] in {'"', "'"}:
        return value[1:-1]
    return value


def parse_inline_list(value: str) -> list[str]:
    if not value.strip():
        return []
    return [unquote(item.strip()) for item in value.split(",") if item.strip()]


def list_field(frontmatter: dict[str, Any], name: str) -> list[str]:
    value = frontmatter.get(name, [])
    if isinstance(value, list):
        return [str(item) for item in value]
    return [] if value == "" else [str(value)]


def source_cards(root: Path) -> dict[str, Path]:
    cards: dict[str, Path] = {}
    for path in sorted((root / "sources").glob("*.md")):
        frontmatter, _ = parse_frontmatter(path)
        source_id = str(frontmatter.get("id", ""))
        if not source_id:
            raise MarshmallowError(f"Missing source card id: {path}")
        cards[source_id] = path
    return cards


def graph_nodes(root: Path) -> dict[str, dict[str, Any]]:
    nodes: dict[str, dict[str, Any]] = {}
    for path in sorted((root / "graph").glob("*.md")):
        frontmatter, _ = parse_frontmatter(path)
        node_id = str(frontmatter.get("id", ""))
        if not node_id:
            raise MarshmallowError(f"Missing graph node id: {path}")
        frontmatter["_path"] = str(path)
        nodes[node_id] = frontmatter
    return nodes


def sync_workspace_index(root: Path) -> dict[str, Any]:
    workspace = read_workspace(root)
    workspace["source_paths"] = [str(path) for path in source_cards(root).values()]
    workspace["graph_nodes"] = [str(path) for path in sorted((root / "graph").glob("*.md"))]
    write_workspace(root, workspace)
    return workspace


def validate_workspace(root: Path) -> list[str]:
    try:
        workspace = read_workspace(root)
        sources = source_cards(root)
        nodes = graph_nodes(root)
    except MarshmallowError as error:
        return [str(error)]
    errors: list[str] = []
    for node_id, node in nodes.items():
        path = Path(node["_path"])
        missing = REQUIRED_NODE_FIELDS - set(node)
        if missing:
            errors.append(f"{path}: missing fields: {', '.join(sorted(missing))}")
        if node_id != path.stem:
            errors.append(f"{path}: node id must match filename stem")
        if not ID_PATTERN.match(node_id):
            errors.append(f"{path}: node id must use lowercase hyphen-case")
        for field in ("applies_to", "labels"):
            for tag in list_field(node, field):
                if not ID_PATTERN.match(tag):
                    errors.append(f"{path}: {field} tag must use lowercase hyphen-case: {tag!r}")
        for source_id in list_field(node, "source_ids"):
            if source_id not in sources:
                errors.append(f"{path}: missing source reference: {source_id}")
        for related_id in list_field(node, "related_nodes"):
            if related_id not in nodes:
                errors.append(f"{path}: broken related node link: {related_id}")
    listed = {str(Path(path).expanduser()) for path in workspace.get("graph_nodes", [])}
    actual = {str(Path(node["_path"])) for node in nodes.values()}
    if listed and listed != actual:
        errors.append("workspace.json graph_nodes does not match graph/*.md")
    return errors


def mermaid_id(value: str) -> str:
    return "node_" + re.sub(r"[^a-zA-Z0-9_]", "_", value)


def render_graph(root: Path) -> str:
    errors = validate_workspace(root)
    if errors:
        raise MarshmallowError("\n".join(errors))
    nodes = graph_nodes(root)
    lines = [
        "# Marshmallow Personal Skill Graph",
        "",
        "Generated from source-backed alignment insights. Edit canonical nodes under `graph/`, then render again.",
        "",
        "```mermaid",
        "graph TD",
    ]
    for node_id, node in sorted(nodes.items()):
        label = str(node.get("insight", "")).replace('"', "'").replace("\n", " ")
        lines.append(f'  {mermaid_id(node_id)}["{label}"]')
    for node_id, node in sorted(nodes.items()):
        for related_id in sorted(list_field(node, "related_nodes")):
            if node_id < related_id:
                lines.append(f"  {mermaid_id(node_id)} --- {mermaid_id(related_id)}")
    lines.extend(["```", "", "## Nodes", "", "| Node | Labels | Insight | Sources | Skills |", "| --- | --- | --- | --- | --- |"])
    for node_id, node in sorted(nodes.items()):
        sources = ", ".join(f"`{item}`" for item in list_field(node, "source_ids")) or "-"
        skills = ", ".join(f"`{item}`" for item in list_field(node, "skills")) or "-"
        labels = ", ".join(f"`{item}`" for item in list_field(node, "labels")) or "-"
        insight = str(node.get("insight", "")).replace("|", "\\|")
        lines.append(f"| [{node_id}](graph/{node_id}.md) | {labels} | {insight} | {sources} | {skills} |")
    return "\n".join(lines) + "\n"
