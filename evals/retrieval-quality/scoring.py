#!/usr/bin/env python3
"""Deterministic fact-level scoring for the retrieval-quality eval.

Ground truth is fact-level: a fact is retrieved when any of its aliases
appears in the retrieved context after normalization (lowercase, collapsed
whitespace). No LLM judge, no network.
"""

from __future__ import annotations

import re
from typing import Any

WHITESPACE = re.compile(r"\s+")

# Lineage states that must never auto-select a plan (the lineage gate).
BLOCKED_LINEAGE = {"drifted", "inactive", "broken"}


def normalize(text: str) -> str:
    return WHITESPACE.sub(" ", text.lower()).strip()


def fact_in_text(fact: dict[str, Any], text: str) -> bool:
    """A fact is contained when any non-empty normalized alias appears in the text."""

    normalized = normalize(text)
    return any(
        normalize(alias) in normalized
        for alias in fact.get("aliases", [])
        if str(alias).strip()
    )


def record_is_relevant(record_text: str, facts: list[dict[str, Any]]) -> bool:
    return any(fact_in_text(fact, record_text) for fact in facts)


def score_query(facts: list[dict[str, Any]], records: list[dict[str, Any]], k: int) -> dict[str, Any]:
    """Fact recall@k, precision@k, and MRR for one retrieval."""

    top = records[:k]
    texts = [str(record.get("text", "")) for record in top]
    joined = " ".join(texts)
    found = [fact for fact in facts if fact_in_text(fact, joined)]
    relevant_flags = [record_is_relevant(text, facts) for text in texts]
    mrr = 0.0
    for index, flag in enumerate(relevant_flags):
        if flag:
            mrr = 1.0 / (index + 1)
            break
    return {
        "recall_at_k": len(found) / len(facts) if facts else 0.0,
        # Precision over the records actually returned (at most k). An empty
        # result list scores 0.0 so missing retrieval is never rewarded.
        "precision_at_k": sum(relevant_flags) / len(top) if top else 0.0,
        "mrr": mrr,
        "facts_found": [str(fact.get("claim", "")) for fact in found],
        "facts_missed": [str(fact.get("claim", "")) for fact in facts if fact not in found],
    }


def score_negative(records: list[dict[str, Any]]) -> dict[str, Any]:
    """Negative-query discipline inputs: did the tool return nothing, or junk?"""

    return {
        "returned": len(records),
        "top_score": float(records[0].get("score", 0)) if records else 0.0,
    }


def score_plan_activation(
    plan_context: dict[str, Any] | None,
    expected_plan: str | None,
    lineage_by_plan: dict[str, str] | None = None,
) -> dict[str, Any] | None:
    """Score one query's plan selection against expectation.

    Matches the plan-centered recall payload shape
    ({"state", "selected_id", "candidates": [{"id", ...}]}). Returns None when
    recall emitted no plan_context, so callers can report "unavailable".
    """

    if plan_context is None:
        return None
    state = str(plan_context.get("state", ""))
    selected = plan_context.get("selected_id")
    candidates = [str(item.get("id", "")) for item in plan_context.get("candidates", [])]
    lineage = str((lineage_by_plan or {}).get(selected, ""))
    return {
        "correct_selection": bool(expected_plan) and selected == expected_plan,
        "false_activation": selected is not None and selected != expected_plan,
        "candidate_surfaced": bool(expected_plan) and state == "candidates" and expected_plan in candidates,
        "lineage_violation": selected is not None and lineage in BLOCKED_LINEAGE,
    }


def mean(values: list[float]) -> float | None:
    values = list(values)
    if not values:
        return None
    return sum(values) / len(values)
