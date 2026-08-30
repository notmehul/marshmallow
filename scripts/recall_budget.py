#!/usr/bin/env python3
"""Estimated-token budgeting for prompt-facing recall responses."""

from __future__ import annotations

import math
from typing import Any

from recall import compact

DEFAULT_TOKEN_BUDGET = 2000
GUIDANCE_BUDGET_SHARE = 0.20
MAX_GUIDANCE_TOKENS = 400


def estimate_tokens(value: str) -> int:
    """Return a dependency-free approximation suitable for response budgeting."""

    text = compact(value)
    return math.ceil(len(text) / 4) if text else 0


def _result_text(result: dict[str, Any]) -> str:
    citations = " ".join(
        f"{source.get('id', '')} {source.get('pointer', '')}" for source in result.get("sources", [])
    )
    return " ".join(
        str(value)
        for value in (
            result.get("id", ""),
            result.get("kind", ""),
            result.get("path", ""),
            result.get("title", ""),
            result.get("insight", ""),
            result.get("task", ""),
            result.get("snippet", ""),
            citations,
        )
    )


def fit_context(results: list[dict[str, Any]], token_budget: int) -> tuple[list[dict[str, Any]], int]:
    fitted: list[dict[str, Any]] = []
    used = 0
    for result in results:
        cost = estimate_tokens(_result_text(result))
        if used + cost > token_budget:
            continue
        fitted.append(result)
        used += cost
    return fitted, used


def trim_to_tokens(value: str, token_budget: int) -> str:
    if token_budget <= 0:
        return ""
    text = compact(value)
    if estimate_tokens(text) <= token_budget:
        return text
    limit = max(1, token_budget * 4 - 3)
    shortened = text[:limit].rsplit(" ", 1)[0].rstrip(" ,;:-")
    return f"{shortened or text[:limit]}..."
