#!/usr/bin/env python3
"""Marshmallow adapter: a thin wrapper over the same recall the CLI calls.

Architecture rule: no second implementation of recall. This module imports
scripts/recall.py and only reshapes its output for the scorer.
"""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(REPO_ROOT / "scripts"))

import recall  # noqa: E402
from base import Adapter  # noqa: E402


class MarshmallowAdapter(Adapter):
    name = "marshmallow"

    def __init__(self) -> None:
        self.root: Path | None = None

    def ingest(self, raw_material_dir: Path) -> Path:
        # A Marshmallow workspace already is the tool's storage format, so
        # ingest is a no-op handle grab.
        self.root = Path(raw_material_dir)
        return self.root

    def retrieve(self, query: str, k: int) -> dict[str, Any]:
        if self.root is None:
            raise RuntimeError("ingest() must run before retrieve()")
        # Plan-centered recall (recall_bundle) may not exist on this branch;
        # fall back to recall_context and report no plan_context.
        if hasattr(recall, "recall_bundle"):
            bundle = recall.recall_bundle(self.root, query, limit=k)
            results = bundle["results"]
            plan_context = bundle["plan_context"]
        else:
            results = recall.recall_context(self.root, query, limit=k)
            plan_context = None
        records = []
        for result in results:
            record = dict(result)
            # Recall returns pointers; the agent then loads the file. The full
            # file text is therefore the retrieved context we score against.
            record["text"] = Path(result["path"]).read_text(encoding="utf-8")
            records.append(record)
        return {"records": records, "plan_context": plan_context}
