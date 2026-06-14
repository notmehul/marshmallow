#!/usr/bin/env python3
"""Read-only context recall over graph, index, and projection Markdown files."""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any

from markdown_graph import graph_nodes, index_pages, list_field, parse_frontmatter, projections
from marshmallow_workspace import MarshmallowError

TOKEN_PATTERN = re.compile(r"[a-z0-9]+")
SNIPPET_LIMIT = 180


def tokenize(value: str) -> list[str]:
    return TOKEN_PATTERN.findall(value.lower())


def compact(value: str) -> str:
    return re.sub(r"\s+", " ", value).strip()


def trim(value: str, limit: int = SNIPPET_LIMIT) -> str:
    text = compact(value)
    if len(text) <= limit:
        return text
    return text[: limit - 1].rstrip() + "..."


def first_heading(body: str) -> str:
    for line in body.splitlines():
        stripped = line.strip()
        if stripped.startswith("# "):
            return stripped.removeprefix("# ").strip()
    return ""


def first_matching_snippet(body: str, tokens: list[str]) -> str:
    lines = [line.strip("- ").strip() for line in body.splitlines() if line.strip()]
    for line in lines:
        line_tokens = set(tokenize(line))
        if any(token in line_tokens for token in tokens):
            return trim(line)
    return trim(" ".join(lines))


def contains_token_phrase(query_tokens: list[str], content_tokens: list[str]) -> bool:
    if not query_tokens or len(query_tokens) > len(content_tokens):
        return False
    phrase_length = len(query_tokens)
    return any(
        content_tokens[index : index + phrase_length] == query_tokens
        for index in range(len(content_tokens) - phrase_length + 1)
    )


def score_record(tokens: list[str], weighted_text: str, body: str) -> int:
    if not tokens:
        return 0
    weighted = weighted_text.lower()
    body_text = body.lower()
    content = f"{weighted} {body_text}"
    content_tokens = tokenize(content)
    weighted_tokens = set(tokenize(weighted))
    body_tokens = set(tokenize(body_text))
    score = 0
    if contains_token_phrase(tokens, content_tokens):
        score += 10
    for token in tokens:
        if token in weighted_tokens:
            score += 5
        if token in body_tokens:
            score += 1
    return score


def record_result(
    *,
    kind: str,
    frontmatter: dict[str, Any],
    body: str,
    tokens: list[str],
) -> dict[str, Any] | None:
    title = str(frontmatter.get("title") or first_heading(body))
    insight = str(frontmatter.get("insight", ""))
    task = str(frontmatter.get("task", ""))
    record_type = str(frontmatter.get("type", ""))
    subjects = list_field(frontmatter, "subjects")
    labels = list_field(frontmatter, "labels")
    skills = list_field(frontmatter, "skills")
    applies_to = list_field(frontmatter, "applies_to")
    graph_ids = list_field(frontmatter, "graph_ids")
    related_nodes = list_field(frontmatter, "related_nodes")
    record_id = str(frontmatter.get("id", ""))
    path = str(frontmatter.get("_path", ""))
    weighted_text = " ".join(
        [
            record_id,
            title,
            insight,
            task,
            record_type,
            " ".join(subjects),
            " ".join(labels),
            " ".join(skills),
            " ".join(applies_to),
            " ".join(graph_ids),
            " ".join(related_nodes),
        ]
    )
    score = score_record(tokens, weighted_text, body)
    if score <= 0:
        return None
    return {
        "id": record_id,
        "kind": kind,
        "path": path,
        "title": title,
        "insight": insight,
        "task": task,
        "type": record_type,
        "subjects": subjects,
        "score": score,
        "snippet": first_matching_snippet(body, tokens),
    }


def read_body(path: str) -> str:
    _, body = parse_frontmatter(Path(path))
    return body


def recall_context(root: Path, query: str, limit: int = 10) -> list[dict[str, Any]]:
    if limit < 1:
        raise MarshmallowError("--limit must be at least 1")
    root = root.expanduser()
    if not root.exists():
        raise MarshmallowError(f"Workspace not found: {root}. Run init first.")

    tokens = tokenize(query)
    if not tokens:
        return []

    results: list[dict[str, Any]] = []
    sources = (
        ("index", index_pages(root)),
        ("recall-packet", projections(root)),
        ("graph", graph_nodes(root)),
    )
    for kind, records in sources:
        for frontmatter in records.values():
            body = read_body(str(frontmatter["_path"]))
            result = record_result(kind=kind, frontmatter=frontmatter, body=body, tokens=tokens)
            if result:
                results.append(result)

    results.sort(key=lambda item: (-int(item["score"]), str(item["kind"]), str(item["id"])))
    return results[:limit]
