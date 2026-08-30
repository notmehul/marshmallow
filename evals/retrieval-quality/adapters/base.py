#!/usr/bin/env python3
"""Adapter interface: one memory tool under evaluation.

Every tool is measured through the same two calls so cross-tool comparison
stays valid regardless of storage shape.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any


ADAPTERS = ("marshmallow", "bm25", "bm25-raw", "embed-graph", "embed-raw", "random")


class Adapter:
    """ingest raw material into the tool, then retrieve context per query.

    retrieve() returns {"records": [...], "plan_context": dict | None}.
    Each record carries at least id, kind, path, score, and text. "text" is
    the context an agent would actually read after this retrieval, and is
    what the scorer matches facts against.
    """

    name = "base"

    def ingest(self, raw_material_dir: Path) -> Path:
        raise NotImplementedError

    def retrieve(self, query: str, k: int) -> dict[str, Any]:
        raise NotImplementedError


def load_adapter(name: str) -> Adapter:
    if name == "marshmallow":
        from marshmallow_adapter import MarshmallowAdapter

        return MarshmallowAdapter()
    if name in {"bm25", "bm25-raw"}:
        from bm25_adapter import Bm25Adapter

        return Bm25Adapter("raw" if name.endswith("-raw") else "graph")
    if name in {"embed-graph", "embed-raw"}:
        from embed_adapter import EmbedAdapter

        return EmbedAdapter(name.split("-", 1)[1])
    if name == "random":
        from random_adapter import RandomAdapter

        return RandomAdapter()
    raise ValueError(f"Unknown adapter: {name!r} (available: {', '.join(ADAPTERS)})")
