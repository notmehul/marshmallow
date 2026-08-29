#!/usr/bin/env python3
"""Random baseline: k graph nodes drawn with a fixed seed, ignoring the query.

Any retrieval number that a random draw can approach is not evidence of
retrieval quality. This row exists so the report always shows that floor.
"""

from __future__ import annotations

import random
from pathlib import Path
from typing import Any

from base import Adapter


class RandomAdapter(Adapter):
    name = "random"

    def __init__(self, seed: int = 0) -> None:
        self.seed = seed
        self.paths: list[Path] = []

    def ingest(self, raw_material_dir: Path) -> Path:
        root = Path(raw_material_dir)
        self.paths = sorted(path for path in (root / "graph").glob("*.md") if path.name != "README.md")
        return root

    def retrieve(self, query: str, k: int) -> dict[str, Any]:
        # Re-seed per query with the query text so the draw is deterministic
        # per query and independent of query order.
        rng = random.Random(f"{self.seed}:{query}")
        chosen = rng.sample(self.paths, min(k, len(self.paths)))
        records = [
            {"id": path.stem, "kind": "graph", "path": str(path), "score": 0, "text": path.read_text(encoding="utf-8")}
            for path in chosen
        ]
        return {"records": records, "plan_context": None}
