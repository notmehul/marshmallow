#!/usr/bin/env python3
"""Shared corpus loading for baseline adapters.

Two corpora, so a retriever can be measured on what Marshmallow stores (the
curated graph nodes) or on what a competing memory tool would ingest (the raw
artifacts the graph was derived from).
"""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any

CORPORA = ("graph", "raw")


def corpus_paths(root: Path, corpus: str) -> list[Path]:
    if corpus not in CORPORA:
        raise ValueError(f"Unknown corpus {corpus!r} (available: {', '.join(CORPORA)})")
    directory = root / corpus
    if not directory.is_dir():
        raise FileNotFoundError(f"{directory}: corpus directory not found")
    return sorted(path for path in directory.glob("*.md") if path.name != "README.md")


def record(path: Path, corpus: str, score: float) -> dict[str, Any]:
    return {
        "id": path.stem,
        "kind": "graph" if corpus == "graph" else "raw",
        "path": str(path),
        "score": round(float(score), 4),
        "text": path.read_text(encoding="utf-8"),
    }


def chunks(text: str, max_words: int = 180) -> list[str]:
    """Paragraph chunks capped by word count, so long files are not silently truncated."""

    out: list[str] = []
    current: list[str] = []
    count = 0
    for paragraph in re.split(r"\n\s*\n", text):
        words = paragraph.split()
        if not words:
            continue
        if current and count + len(words) > max_words:
            out.append(" ".join(current))
            current, count = [], 0
        while len(words) > max_words:
            out.append(" ".join(words[:max_words]))
            words = words[max_words:]
        current.extend(words)
        count += len(words)
    if current:
        out.append(" ".join(current))
    return out or [text.strip()]
