#!/usr/bin/env python3
"""BM25 baseline: stdlib Okapi BM25 over one corpus (graph nodes or raw artifacts).

The reference lexical retriever. Marshmallow's hand-tuned scorer has to beat
this on its own dataset before any of its ranking heuristics count as a win.
Tokenization is shared with scripts/recall.py so the comparison isolates the
scoring function, not the tokenizer.
"""

from __future__ import annotations

import math
import sys
from collections import Counter
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(REPO_ROOT / "scripts"))

from recall import tokenize  # noqa: E402
from base import Adapter  # noqa: E402
from corpus import corpus_paths, record  # noqa: E402

K1 = 1.5
B = 0.75


class Bm25Adapter(Adapter):
    def __init__(self, corpus: str = "graph") -> None:
        self.corpus = corpus
        self.name = "bm25" if corpus == "graph" else f"bm25-{corpus}"
        self.docs: list[tuple[Path, Counter[str], int]] = []
        self.df: Counter[str] = Counter()
        self.avg_len = 0.0

    def ingest(self, raw_material_dir: Path) -> Path:
        root = Path(raw_material_dir)
        self.docs = []
        self.df = Counter()
        for path in corpus_paths(root, self.corpus):
            tokens = tokenize(path.read_text(encoding="utf-8"))
            counts = Counter(tokens)
            self.docs.append((path, counts, len(tokens)))
            self.df.update(counts.keys())
        self.avg_len = sum(length for _, _, length in self.docs) / len(self.docs) if self.docs else 0.0
        return root

    def _idf(self, term: str) -> float:
        n = len(self.docs)
        df = self.df.get(term, 0)
        return math.log(1 + (n - df + 0.5) / (df + 0.5))

    def retrieve(self, query: str, k: int) -> dict[str, Any]:
        terms = tokenize(query)
        scored: list[tuple[float, Path]] = []
        for path, counts, length in self.docs:
            score = 0.0
            for term in terms:
                tf = counts.get(term, 0)
                if not tf:
                    continue
                norm = tf * (K1 + 1) / (tf + K1 * (1 - B + B * length / self.avg_len))
                score += self._idf(term) * norm
            if score > 0:
                scored.append((score, path))
        scored.sort(key=lambda item: (-item[0], item[1].stem))
        records = [record(path, self.corpus, score) for score, path in scored[:k]]
        return {"records": records, "plan_context": None}
