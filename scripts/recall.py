#!/usr/bin/env python3
"""Read-only context recall over graph, index, and projection Markdown files."""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any

from markdown_graph import graph_nodes, index_pages, list_field, parse_frontmatter, projections, readable_source_cards
from marshmallow_workspace import MarshmallowError
from record_access import managed_lineage_status

TOKEN_PATTERN = re.compile(r"[a-z0-9]+")
SNIPPET_LIMIT = 180
PLAN_CANDIDATE_LIMIT = 3
PLAN_CONNECTED_LIMIT = 4
PLAN_ACTIVATION_STOPWORDS = set(
    "a an and are as at be by context for from in is it of on or plan plans task the this to with work".split()
)


def tokenize(value: str) -> list[str]:
    return TOKEN_PATTERN.findall(value.lower())


def plan_activation_tokens(tokens: list[str]) -> list[str]:
    return [token for token in tokens if token not in PLAN_ACTIVATION_STOPWORDS]


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


def cite_sources(
    frontmatter: dict[str, Any],
    sources_by_id: dict[str, dict[str, Any]],
) -> list[dict[str, str]]:
    """Resolve a node's source_ids to {id, pointer} so recall is auditable.

    This is the wedge: every recalled fact carries the immutable source it came
    from. Unresolved ids are still listed (pointer empty) so a broken provenance
    link is visible rather than silently dropped.
    """

    citations: list[dict[str, str]] = []
    for source_id in list_field(frontmatter, "source_ids"):
        source = sources_by_id.get(source_id, {})
        citations.append({"id": source_id, "pointer": str(source.get("pointer", ""))})
    return citations


def record_result(
    *,
    kind: str,
    frontmatter: dict[str, Any],
    body: str,
    tokens: list[str],
    activation_tokens: list[str],
    sources_by_id: dict[str, dict[str, Any]],
) -> dict[str, Any]:
    title = str(frontmatter.get("title") or first_heading(body))
    insight = str(frontmatter.get("insight", ""))
    task = str(frontmatter.get("task", ""))
    record_type = str(frontmatter.get("type", ""))
    status = str(frontmatter.get("status", ""))
    managed = str(frontmatter.get("managed", "")).strip() == "true"
    subjects = list_field(frontmatter, "subjects")
    labels = list_field(frontmatter, "labels")
    skills = list_field(frontmatter, "skills")
    applies_to = list_field(frontmatter, "applies_to")
    graph_ids = list_field(frontmatter, "graph_ids")
    related_nodes = list_field(frontmatter, "related_nodes")
    guidance = str(frontmatter.get("guidance", ""))
    guidance_examples = list_field(frontmatter, "guidance_examples")
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
            guidance,
            " ".join(guidance_examples),
        ]
    )
    score = score_record(tokens, weighted_text, body)
    activation_score = score_record(activation_tokens, weighted_text, body)
    metadata_activation_score = score_record(activation_tokens, weighted_text, "")
    return {
        "id": record_id,
        "kind": kind,
        "path": path,
        "title": title,
        "insight": insight,
        "task": task,
        "type": record_type,
        "status": status,
        "managed": managed,
        "subjects": subjects,
        "graph_ids": graph_ids,
        "related_nodes": related_nodes,
        "score": score,
        "direct_score": score,
        "activation_score": activation_score,
        "metadata_activation_score": metadata_activation_score,
        "bundle_id": None,
        "distance": None,
        "match_reason": "direct",
        "role": "direct",
        "lineage_status": "not-managed",
        "snippet": first_matching_snippet(body, tokens),
        "sources": cite_sources(frontmatter, sources_by_id) if kind == "graph" else [],
    }


def read_body(path: str) -> str:
    _, body = parse_frontmatter(Path(path))
    return body


def graph_adjacency(nodes: dict[str, dict[str, Any]]) -> dict[str, list[str]]:
    """Return ordered bidirectional graph links without changing stored files."""

    adjacency = {node_id: [] for node_id in nodes}
    for node_id, node in nodes.items():
        for related_id in list_field(node, "related_nodes"):
            if related_id not in adjacency:
                continue
            if related_id not in adjacency[node_id]:
                adjacency[node_id].append(related_id)
            if node_id not in adjacency[related_id]:
                adjacency[related_id].append(node_id)
    return adjacency


def link_local_plan_scores(
    records_with_bodies: list[tuple[dict[str, Any], str]],
    activation_tokens: list[str],
) -> dict[str, int]:
    """Credit navigation pages only for the line that links a graph node."""

    scores: dict[str, int] = {}
    for result, body in records_with_bodies:
        if result["kind"] not in {"index", "recall-packet"}:
            continue
        for line in body.splitlines():
            for graph_id in result["graph_ids"]:
                if f"[[{graph_id}]]" not in line:
                    continue
                score = score_record(activation_tokens, graph_id, line)
                if score:
                    scores[graph_id] = max(scores.get(graph_id, 0), score)
    return scores


def plan_candidates(
    graph_results: dict[str, dict[str, Any]],
    adjacency: dict[str, list[str]],
    link_scores: dict[str, int],
    strongest_node_ids: set[str],
    strongest_link_ids: set[str],
) -> list[dict[str, Any]]:
    """Return active plans supported by metadata or the strongest linked context."""

    candidates: list[dict[str, Any]] = []
    for node_id, result in graph_results.items():
        if result["type"] != "plan" or result["status"] != "active" or not result["managed"]:
            continue
        if result["lineage_status"] in {"broken", "drifted"}:
            continue
        # A plan becomes the hub only when it is already the strongest graph
        # match by ordinary scoring AND its own concise metadata matches the
        # query. The eval showed every weaker activation path (any positive
        # metadata overlap, connected-node strength, linked navigation lines)
        # let one broadly linked plan hijack rank one on 15+ of 40 unrelated
        # queries; plan centering must never outrank a better direct answer.
        strongest_direct = max(
            (int(item["direct_score"]) for item in graph_results.values()), default=0
        )
        relevance = int(result["direct_score"])
        reason = "direct-plan"
        if relevance <= 0 or relevance < strongest_direct or int(result["metadata_activation_score"]) <= 0:
            continue
        candidates.append({"id": node_id, "score": relevance, "reason": reason})
    candidates.sort(key=lambda item: (-int(item["score"]), str(item["id"])))
    return candidates[:PLAN_CANDIDATE_LIMIT]


def strongest_ids(scores: dict[str, int]) -> set[str]:
    strongest = max(scores.values(), default=0)
    if strongest <= 0:
        return set()
    return {record_id for record_id, score in scores.items() if score == strongest}


def _selected_plan_results(
    plan_id: str,
    relevance: int,
    graph_results: dict[str, dict[str, Any]],
    direct_results: list[dict[str, Any]],
    adjacency: dict[str, list[str]],
    limit: int,
) -> list[dict[str, Any]]:
    plan = dict(graph_results[plan_id])
    plan.update(
        score=relevance,
        bundle_id=plan_id,
        distance=0,
        match_reason="plan-hub",
        role="plan-hub",
    )

    bundle = [plan]
    seen = {plan_id}
    for original in sorted(
        direct_results,
        key=lambda item: (-int(item["score"]), str(item["kind"]), str(item["id"])),
    ):
        result_key = f"{original['kind']}:{original['id']}"
        if original["kind"] == "graph" and original["id"] in seen:
            continue
        result = dict(original)
        if original["kind"] == "graph" and original["id"] in adjacency[plan_id]:
            result.update(
                bundle_id=plan_id,
                distance=1,
                match_reason="direct-and-connected",
                role="direct-and-connected",
            )
        bundle.append(result)
        seen.add(original["id"] if original["kind"] == "graph" else result_key)
        if len(bundle) >= limit:
            return bundle[:limit]

    neighbor_order = {node_id: index for index, node_id in enumerate(adjacency[plan_id])}
    neighbors = [graph_results[node_id] for node_id in adjacency[plan_id] if node_id not in seen]
    neighbors.sort(key=lambda item: (-int(item["direct_score"]), neighbor_order[item["id"]]))
    for original in neighbors[:PLAN_CONNECTED_LIMIT]:
        result = dict(original)
        result.update(
            bundle_id=plan_id,
            distance=1,
            match_reason="connected-to-plan",
            role="connected-to-plan",
        )
        bundle.append(result)
        if len(bundle) >= limit:
            break
    return bundle[:limit]


def _candidate_plan_results(
    candidates: list[dict[str, Any]],
    graph_results: dict[str, dict[str, Any]],
    direct_results: list[dict[str, Any]],
    limit: int,
) -> list[dict[str, Any]]:
    results: list[dict[str, Any]] = []
    seen_graph_ids: set[str] = set()
    for candidate in candidates:
        result = dict(graph_results[str(candidate["id"])])
        result.update(
            score=int(candidate["score"]),
            match_reason="plan-candidate",
            role="plan-candidate",
        )
        results.append(result)
        seen_graph_ids.add(str(candidate["id"]))
    for original in sorted(
        direct_results,
        key=lambda item: (-int(item["score"]), str(item["kind"]), str(item["id"])),
    ):
        if original["kind"] == "graph" and original["id"] in seen_graph_ids:
            continue
        results.append(original)
        if len(results) >= limit:
            break
    return results[:limit]


def recall_bundle(root: Path, query: str, limit: int = 10) -> dict[str, Any]:
    if limit < 1:
        raise MarshmallowError("--limit must be at least 1")
    root = root.expanduser()
    if not root.exists():
        raise MarshmallowError(f"Workspace not found: {root}. Run init first.")

    tokens = tokenize(query)
    if not tokens:
        return {
            "query": query,
            "plan_context": {"state": "none", "selected_id": None, "candidates": []},
            "results": [],
        }
    activation_tokens = plan_activation_tokens(tokens)

    sources_by_id = readable_source_cards(root)

    all_results: list[dict[str, Any]] = []
    records_with_bodies: list[tuple[dict[str, Any], str]] = []
    graph_records = graph_nodes(root)
    sources = (
        ("index", index_pages(root)),
        ("recall-packet", projections(root)),
        ("graph", graph_records),
    )
    for kind, records in sources:
        for frontmatter in records.values():
            body = read_body(str(frontmatter["_path"]))
            result = record_result(
                kind=kind,
                frontmatter=frontmatter,
                body=body,
                tokens=tokens,
                activation_tokens=activation_tokens,
                sources_by_id=sources_by_id,
            )
            if kind == "graph":
                result["lineage_status"] = managed_lineage_status(
                    root,
                    result["id"],
                    frontmatter,
                    sources=sources_by_id,
                )["status"]
            all_results.append(result)
            records_with_bodies.append((result, body))

    direct_results = [result for result in all_results if int(result["direct_score"]) > 0]
    graph_results = {result["id"]: result for result in all_results if result["kind"] == "graph"}
    adjacency = graph_adjacency(graph_records)
    link_scores = link_local_plan_scores(records_with_bodies, activation_tokens)
    node_scores = {
        node_id: int(result["activation_score"])
        for node_id, result in graph_results.items()
        if result["type"] != "plan" and int(result["activation_score"]) > 0
    }
    candidates = plan_candidates(
        graph_results,
        adjacency,
        link_scores,
        strongest_ids(node_scores),
        strongest_ids(link_scores),
    )
    if len(candidates) == 1:
        selected_id = str(candidates[0]["id"])
        results = _selected_plan_results(
            selected_id,
            int(candidates[0]["score"]),
            graph_results,
            direct_results,
            adjacency,
            limit,
        )
        plan_context = {"state": "selected", "selected_id": selected_id, "candidates": candidates}
    elif candidates:
        results = _candidate_plan_results(candidates, graph_results, direct_results, limit)
        plan_context = {"state": "candidates", "selected_id": None, "candidates": candidates}
    else:
        direct_results.sort(key=lambda item: (-int(item["score"]), str(item["kind"]), str(item["id"])))
        results = direct_results[:limit]
        plan_context = {"state": "none", "selected_id": None, "candidates": []}
    for result in results:
        result.pop("activation_score", None)
        result.pop("metadata_activation_score", None)
    return {"query": query, "plan_context": plan_context, "results": results}


def recall_context(root: Path, query: str, limit: int = 10) -> list[dict[str, Any]]:
    """Backward-compatible result-list API."""

    return recall_bundle(root, query, limit=limit)["results"]
