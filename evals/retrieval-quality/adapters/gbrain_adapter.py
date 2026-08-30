#!/usr/bin/env python3
"""GBrain adapter: shells out to the ``gbrain`` CLI against a PGLite brain.

``gbrain import raw/`` stores each artifact as a page and embeds it;
``gbrain query --json`` runs GBrain's hybrid search (keyword + vector, RRF).
The ``gbrain`` variant passes ``--no-expand`` so only the retriever is
measured; ``gbrain-expand`` keeps GBrain's LLM query expansion on, which is
how it ships.

Needs the ``gbrain`` binary on PATH and a brain initialised under
GBRAIN_HOME with an embedding provider, e.g.

    GBRAIN_HOME=... GOOGLE_GENERATIVE_AI_API_KEY=... \\
      gbrain init --pglite --non-interactive --path $GBRAIN_HOME/brain.pglite \\
      --embedding-model google:gemini-embedding-001 --embedding-dimensions 768

Ingest is skipped when the brain already holds pages, so reruns do not
re-embed. Point GBRAIN_HOME at a scratch directory; never at a real brain.
"""

from __future__ import annotations

import json
import os
import shutil
import subprocess
from pathlib import Path
from typing import Any

from base import Adapter
from corpus import corpus_paths


class GbrainAdapter(Adapter):
    def __init__(self, expand: bool = False) -> None:
        self.expand = expand
        self.name = "gbrain-expand" if expand else "gbrain"
        self.corpus = "raw"
        self.root: Path | None = None

    def _run(self, *args: str, cwd: Path | None = None) -> str:
        if not shutil.which("gbrain"):
            raise RuntimeError("the gbrain adapter needs the gbrain CLI on PATH (bun install -g github:garrytan/gbrain)")
        if not os.environ.get("GBRAIN_HOME"):
            raise RuntimeError("set GBRAIN_HOME to a scratch brain directory before running the gbrain adapter")
        result = subprocess.run(["gbrain", *args], cwd=cwd, capture_output=True, text=True, check=False)
        if result.returncode != 0:
            raise RuntimeError(f"gbrain {' '.join(args[:2])} failed: {result.stderr.strip()[:300]}")
        return result.stdout

    def _page_count(self) -> int:
        listing = self._run("list", "--limit", "5")
        return sum(1 for line in listing.splitlines() if line.strip() and "\t" in line)

    def ingest(self, raw_material_dir: Path) -> Path:
        root = Path(raw_material_dir)
        self.root = root
        corpus_paths(root, self.corpus)  # fail early if raw/ is missing
        if self._page_count() == 0:
            self._run("import", "./raw", cwd=root)
        return root

    def retrieve(self, query: str, k: int) -> dict[str, Any]:
        args = ["query", query, "--json"]
        if not self.expand:
            args.append("--no-expand")
        payload = json.loads(self._run(*args, cwd=self.root) or "[]")
        records = []
        for item in payload[:k]:
            slug = str(item.get("slug", ""))
            records.append(
                {
                    "id": slug,
                    "kind": "raw",
                    "path": str(self.root / "raw" / f"{slug}.md") if self.root else "",
                    "score": float(item.get("score") or 0.0),
                    "text": str(item.get("chunk_text", "")),
                }
            )
        return {"records": records, "plan_context": None}
