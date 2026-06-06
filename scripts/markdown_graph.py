#!/usr/bin/env python3
"""Markdown source-card and graph-node parsing/validation."""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any

from marshmallow_workspace import MarshmallowError, atomic_write, ensure_workspace, iso_timestamp, timestamp
from safety import validate_generated_guidance

REQUIRED_NODE_FIELDS = {"id", "insight", "source_ids"}
REQUIRED_SOURCE_FIELDS = {"id", "pointer", "captured"}
ID_PATTERN = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
SLUG_PATTERN = re.compile(r"[^a-z0-9]+")
GENERIC_INSIGHT_PATTERNS = (
    re.compile(r"\bprefer clarity\b", re.IGNORECASE),
    re.compile(r"\bavoid complexity\b", re.IGNORECASE),
    re.compile(r"\bbe thoughtful\b", re.IGNORECASE),
    re.compile(r"\bhigh quality\b", re.IGNORECASE),
    re.compile(r"\bmake it better\b", re.IGNORECASE),
)


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


def source_cards(root: Path) -> dict[str, dict[str, Any]]:
    cards: dict[str, dict[str, Any]] = {}
    for path in sorted((root / "sources").glob("*.md")):
        frontmatter, _ = parse_frontmatter(path)
        source_id = str(frontmatter.get("id", ""))
        if not source_id:
            raise MarshmallowError(f"Missing source card id: {path}")
        if source_id in cards:
            raise MarshmallowError(f"Duplicate source card id {source_id!r}: {path}")
        frontmatter["_path"] = str(path)
        cards[source_id] = frontmatter
    return cards


def graph_nodes(root: Path) -> dict[str, dict[str, Any]]:
    nodes: dict[str, dict[str, Any]] = {}
    for path in sorted((root / "graph").glob("*.md")):
        frontmatter, _ = parse_frontmatter(path)
        node_id = str(frontmatter.get("id", ""))
        if not node_id:
            raise MarshmallowError(f"Missing graph node id: {path}")
        if node_id in nodes:
            raise MarshmallowError(f"Duplicate graph node id {node_id!r}: {path}")
        frontmatter["_path"] = str(path)
        nodes[node_id] = frontmatter
    return nodes


def section_text(body: str, heading: str) -> str:
    pattern = re.compile(rf"^## {re.escape(heading)}\s*$", re.MULTILINE)
    match = pattern.search(body)
    if not match:
        return ""
    next_heading = re.search(r"^##\s+", body[match.end() :], re.MULTILINE)
    end = match.end() + next_heading.start() if next_heading else len(body)
    return body[match.end() : end].strip()


def evidence_is_thin(evidence: str) -> bool:
    compact = re.sub(r"\s+", " ", evidence).strip()
    if len(compact) < 80:
        return True
    placeholders = ("explain the evidence", "source-example", "selected details")
    return any(placeholder in compact.lower() for placeholder in placeholders)


def graph_quality_warnings(root: Path) -> list[str]:
    """Return non-blocking warnings for graph nodes that may not change behavior."""

    root = ensure_workspace(root)
    warnings: list[str] = []
    try:
        nodes = graph_nodes(root)
    except MarshmallowError as error:
        return [str(error)]

    for node_id, node in nodes.items():
        path = Path(node["_path"])
        try:
            _, body = parse_frontmatter(path)
        except MarshmallowError as error:
            warnings.append(str(error))
            continue

        insight = str(node.get("insight", "")).strip()
        if any(pattern.search(insight) for pattern in GENERIC_INSIGHT_PATTERNS):
            warnings.append(f"{path}: insight may be too generic to change agent behavior")

        related_nodes = list_field(node, "related_nodes")
        if related_nodes and "[[" not in body:
            warnings.append(f"{path}: related_nodes should also appear as Obsidian [[links]] in the body")

        if evidence_is_thin(section_text(body, "Evidence")):
            warnings.append(f"{path}: evidence section looks too thin for durable alignment")

        if not list_field(node, "skills"):
            warnings.append(f"{path}: node is not tied to any skill; it may not affect agent behavior")
    return warnings


def validate_workspace(root: Path) -> list[str]:
    root = ensure_workspace(root)
    errors: list[str] = []
    try:
        sources = source_cards(root)
        nodes = graph_nodes(root)
    except MarshmallowError as error:
        return [str(error)]

    for source_id, source in sources.items():
        path = Path(source["_path"])
        missing = REQUIRED_SOURCE_FIELDS - set(source)
        if missing:
            errors.append(f"{path}: missing fields: {', '.join(sorted(missing))}")
        if source_id != path.stem:
            errors.append(f"{path}: source id must match filename stem")
        if not ID_PATTERN.match(source_id):
            errors.append(f"{path}: source id must use lowercase hyphen-case")
        raw_pointer = source.get("pointer", "")
        pointer = raw_pointer.strip() if isinstance(raw_pointer, str) else ""
        if not pointer:
            errors.append(f"{path}: source pointer must be non-empty")
        raw_captured = source.get("captured", "")
        captured = raw_captured.strip() if isinstance(raw_captured, str) else ""
        if not captured:
            errors.append(f"{path}: captured must be non-empty")
        for label in list_field(source, "labels"):
            if not ID_PATTERN.match(label):
                errors.append(f"{path}: labels tag must use lowercase hyphen-case: {label!r}")

    for node_id, node in nodes.items():
        path = Path(node["_path"])
        missing = REQUIRED_NODE_FIELDS - set(node)
        if missing:
            errors.append(f"{path}: missing fields: {', '.join(sorted(missing))}")
        if node_id != path.stem:
            errors.append(f"{path}: node id must match filename stem")
        if not ID_PATTERN.match(node_id):
            errors.append(f"{path}: node id must use lowercase hyphen-case")
        insight = str(node.get("insight", "")).strip()
        if not insight:
            errors.append(f"{path}: insight must be non-empty")
        else:
            try:
                validate_generated_guidance(insight, path, max_chars=600)
            except MarshmallowError as error:
                errors.append(str(error))
        source_ids = list_field(node, "source_ids")
        if not source_ids:
            errors.append(f"{path}: source_ids must include at least one source id")
        for field in ("applies_to", "labels", "skills"):
            for tag in list_field(node, field):
                if not ID_PATTERN.match(tag):
                    errors.append(f"{path}: {field} tag must use lowercase hyphen-case: {tag!r}")
        for source_id in source_ids:
            if source_id not in sources:
                errors.append(f"{path}: missing source reference: {source_id}")
        for related_id in list_field(node, "related_nodes"):
            if not ID_PATTERN.match(related_id):
                errors.append(f"{path}: related_nodes tag must use lowercase hyphen-case: {related_id!r}")
            elif related_id not in nodes:
                errors.append(f"{path}: broken related node link: {related_id}")
    return errors


def slugify(value: str, fallback: str = "correction") -> str:
    normalized = SLUG_PATTERN.sub("-", value.lower()).strip("-")
    return normalized or fallback


def write_user_correction_source(
    root: Path,
    title: str,
    content: str,
    cwd: str | None = None,
) -> Path:
    """Create a source card for an explicit user correction."""

    root = ensure_workspace(root)
    source_id = f"user-correction-{timestamp().lower()}-{slugify(title)}"
    path = root / "sources" / f"{source_id}.md"
    if path.exists():
        raise MarshmallowError(f"Correction source already exists: {path}")
    cwd_line = f"cwd: {cwd}\n" if cwd else ""
    card = f"""---
id: {source_id}
pointer: user-correction:{source_id}
captured: {iso_timestamp()}
summary: {title}
labels: [user-correction]
{cwd_line}---

# {title}

{content.strip()}
"""
    atomic_write(path, card)
    return path
