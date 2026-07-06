#!/usr/bin/env python3
"""Add compact personal guidance to source-backed recall results."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from markdown_graph import graph_nodes, list_field, parse_frontmatter, section_text
from marshmallow_workspace import MarshmallowError
from recall import compact, recall_bundle, score_record, tokenize
from recall_budget import (
    DEFAULT_TOKEN_BUDGET,
    GUIDANCE_BUDGET_SHARE,
    MAX_GUIDANCE_TOKENS,
    estimate_tokens,
    fit_context,
    trim_to_tokens,
)

MAX_GUIDANCE_ITEMS = 3
MIN_GUIDANCE_TOKENS = 6

EXCLUDED_STATUSES = {"archived", "historical", "inactive", "rejected", "superseded"}
STOPWORDS = {
    "a",
    "an",
    "and",
    "are",
    "as",
    "at",
    "be",
    "before",
    "for",
    "from",
    "how",
    "i",
    "in",
    "is",
    "it",
    "of",
    "on",
    "or",
    "should",
    "the",
    "this",
    "to",
    "we",
    "what",
    "when",
    "with",
}
EXAMPLE_SECTIONS = ("Use In Work", "How to apply", "Rule", "Use In Skills")


def _alignment_enabled(node: dict[str, Any]) -> bool:
    alignment = str(node.get("alignment", "")).strip().lower()
    if alignment == "false":
        return False
    return bool(
        alignment == "true"
        or str(node.get("guidance", "")).strip()
        or list_field(node, "guidance_examples")
        or str(node.get("type", "")).strip() == "preference"
    )


def _meaningful_query_tokens(query: str) -> list[str]:
    return [token for token in tokenize(query) if token not in STOPWORDS]


def _guidance_metadata(node: dict[str, Any]) -> str:
    return " ".join(
        [
            str(node.get("id", "")),
            str(node.get("insight", "")),
            str(node.get("guidance", "")),
            " ".join(list_field(node, "guidance_examples")),
            " ".join(list_field(node, "subjects")),
            " ".join(list_field(node, "labels")),
            " ".join(list_field(node, "skills")),
            " ".join(list_field(node, "applies_to")),
        ]
    )


def _section_example(body: str) -> str:
    for heading in EXAMPLE_SECTIONS:
        section = section_text(body, heading)
        if section:
            return compact(section.removeprefix("- "))
    return ""


def _candidate(node: dict[str, Any], query_tokens: list[str]) -> dict[str, Any] | None:
    if not _alignment_enabled(node):
        return None
    if str(node.get("status", "")).strip().lower() in EXCLUDED_STATUSES:
        return None

    metadata = _guidance_metadata(node)
    if not set(query_tokens).intersection(tokenize(metadata)):
        return None

    path = Path(str(node["_path"]))
    _, body = parse_frontmatter(path)
    score = score_record(query_tokens, metadata, body)
    if score <= 0:
        return None

    examples = list_field(node, "guidance_examples")
    example = examples[0].strip() if examples else _section_example(body)
    return {
        "id": str(node.get("id", "")),
        "guidance": str(node.get("guidance") or node.get("insight", "")).strip(),
        "example": example,
        "score": score,
    }


def _fit_guidance(
    candidates: list[dict[str, Any]],
    token_budget: int,
    limit: int = MAX_GUIDANCE_ITEMS,
) -> tuple[list[dict[str, Any]], int]:
    fitted: list[dict[str, Any]] = []
    used = 0
    for candidate in candidates:
        if len(fitted) >= limit:
            break
        remaining = token_budget - used
        if remaining < MIN_GUIDANCE_TOKENS:
            break

        fixed_text = f"{candidate['id']} {candidate['score']}"
        fixed_cost = estimate_tokens(fixed_text)
        content_budget = remaining - fixed_cost
        if content_budget < MIN_GUIDANCE_TOKENS:
            continue

        item = dict(candidate)
        has_example = bool(str(candidate["example"]).strip())
        example_budget = content_budget * 2 // 5 if has_example else 0
        guidance_budget = content_budget - example_budget
        item["guidance"] = trim_to_tokens(str(candidate["guidance"]), guidance_budget)
        item["example"] = trim_to_tokens(str(candidate["example"]), example_budget)
        cost = estimate_tokens(f"{fixed_text} {item['guidance']} {item['example']}")
        if not item["guidance"] or used + cost > token_budget:
            continue
        fitted.append(item)
        used += cost
    return fitted, used


def recall_with_personal_guidance(
    root: Path,
    query: str,
    *,
    limit: int = 10,
    token_budget: int = DEFAULT_TOKEN_BUDGET,
) -> dict[str, Any]:
    """Return relevant context plus a tightly bounded personal-guidance layer."""

    if token_budget < 1:
        raise MarshmallowError("token budget must be at least 1")

    guidance_budget = min(MAX_GUIDANCE_TOKENS, int(token_budget * GUIDANCE_BUDGET_SHARE))

    query_tokens = _meaningful_query_tokens(query)
    candidates = [
        candidate
        for node in graph_nodes(root).values()
        if query_tokens and (candidate := _candidate(node, query_tokens)) is not None
    ]
    candidates.sort(key=lambda item: (-int(item["score"]), str(item["id"])))
    guidance, guidance_tokens = _fit_guidance(candidates, guidance_budget)

    # A node in the guidance layer is not repeated as an ordinary result: the
    # guidance line (still resolvable by graph id) is its representation, so
    # the same record never spends the budget twice.
    guidance_ids = {item["id"] for item in guidance}
    context_budget = token_budget - guidance_tokens
    inner = recall_bundle(root, query, limit=limit)
    raw_results = [
        result
        for result in inner["results"]
        if not (result["kind"] == "graph" and result["id"] in guidance_ids)
    ]
    results, context_tokens = fit_context(raw_results, context_budget)
    total_tokens = context_tokens + guidance_tokens
    guidance_share = guidance_tokens / total_tokens if total_tokens else 0.0

    return {
        "results": results,
        "plan_context": inner["plan_context"],
        "personal_guidance": guidance,
        "budget": {
            "token_budget": token_budget,
            "estimated_context_tokens": context_tokens,
            "personal_guidance_token_budget": guidance_budget,
            "estimated_personal_guidance_tokens": guidance_tokens,
            "estimated_personal_guidance_share": round(guidance_share, 3),
        },
    }
