#!/usr/bin/env python3
"""Dense-embedding baseline: local ONNX embeddings, cosine similarity, no API key.

This is the retrieval class that hosted memory tools (Mem0, MemMachine, GBrain)
use under the hood, so it answers the question a competitor row would answer:
does semantic matching survive paraphrase where lexical scoring collapses?

Requires the optional ``fastembed`` package (``uv pip install fastembed``);
the model (BAAI/bge-small-en-v1.5, 384d) downloads once. Files are embedded as
paragraph chunks and a document scores by its best chunk, which is what chunked
vector stores do. Marshmallow itself stays dependency-free; only this adapter
imports fastembed.
"""

from __future__ import annotations

import math
from pathlib import Path
from typing import Any

from base import Adapter
from corpus import chunks, corpus_paths, record

MODEL = "BAAI/bge-small-en-v1.5"


def _cosine(a: list[float], b: list[float]) -> float:
    dot = sum(x * y for x, y in zip(a, b))
    na = math.sqrt(sum(x * x for x in a))
    nb = math.sqrt(sum(y * y for y in b))
    return dot / (na * nb) if na and nb else 0.0


class EmbedAdapter(Adapter):
    def __init__(self, corpus: str = "graph") -> None:
        self.corpus = corpus
        self.name = f"embed-{corpus}"
        self.model: Any = None
        self.docs: list[tuple[Path, list[list[float]]]] = []

    def _load_model(self) -> Any:
        if self.model is None:
            try:
                from fastembed import TextEmbedding
            except ImportError as error:  # pragma: no cover - environment-dependent
                raise RuntimeError(
                    "the embed adapter needs the optional fastembed package: uv pip install fastembed"
                ) from error
            self.model = TextEmbedding(MODEL)
        return self.model

    def ingest(self, raw_material_dir: Path) -> Path:
        root = Path(raw_material_dir)
        model = self._load_model()
        self.docs = []
        paths = corpus_paths(root, self.corpus)
        pieces: list[str] = []
        spans: list[tuple[int, int]] = []
        for path in paths:
            parts = chunks(path.read_text(encoding="utf-8"))
            spans.append((len(pieces), len(pieces) + len(parts)))
            pieces.extend(parts)
        vectors = [list(map(float, vector)) for vector in model.embed(pieces, batch_size=64)]
        for path, (start, end) in zip(paths, spans):
            self.docs.append((path, vectors[start:end]))
        return root

    def retrieve(self, query: str, k: int) -> dict[str, Any]:
        model = self._load_model()
        query_vector = list(map(float, next(iter(model.embed([query])))))
        scored = [
            (max(_cosine(query_vector, vector) for vector in vectors), path)
            for path, vectors in self.docs
        ]
        scored.sort(key=lambda item: (-item[0], item[1].stem))
        records = [record(path, self.corpus, score) for score, path in scored[:k]]
        return {"records": records, "plan_context": None}
