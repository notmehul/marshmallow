#!/usr/bin/env python3
"""Hosted-embedding baseline: Google gemini-embedding-001 over one corpus.

The same chunking and best-chunk cosine as the local embed adapter, with a
large hosted embedder in place of bge-small. This is the row that answers
whether a stronger embedding model closes the paraphrase gap.

Needs GEMINI_API_KEY in the environment. Stdlib only (urllib). Embeddings are
cached on disk under EVAL_EMBED_CACHE (default: a cache/ directory beside this
file, gitignored) keyed by model, task type, and text hash, so reruns and
scaled tiers that share files do not re-bill.
"""

from __future__ import annotations

import hashlib
import json
import math
import os
import time
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any

from base import Adapter
from corpus import chunks, corpus_paths, record

MODEL = "gemini-embedding-001"
ENDPOINT = f"https://generativelanguage.googleapis.com/v1beta/models/{MODEL}:batchEmbedContents"
BATCH = 100
DIMENSIONS = 768  # gemini-embedding-001 supports Matryoshka truncation; 768 keeps cache and cosine cheap.


def _cosine(a: list[float], b: list[float]) -> float:
    dot = sum(x * y for x, y in zip(a, b))
    na = math.sqrt(sum(x * x for x in a))
    nb = math.sqrt(sum(y * y for y in b))
    return dot / (na * nb) if na and nb else 0.0


class GeminiEmbedAdapter(Adapter):
    def __init__(self, corpus: str = "graph") -> None:
        self.corpus = corpus
        self.name = f"gemini-{corpus}"
        self.docs: list[tuple[Path, list[list[float]]]] = []
        self.cache_dir = Path(os.environ.get("EVAL_EMBED_CACHE", Path(__file__).resolve().parent.parent / "cache"))
        self.calls = 0

    def _key(self) -> str:
        key = os.environ.get("GEMINI_API_KEY", "")
        if not key:
            raise RuntimeError("the gemini adapter needs GEMINI_API_KEY in the environment")
        return key

    def _cache_path(self, task: str, text: str) -> Path:
        digest = hashlib.sha256(f"{MODEL}\n{DIMENSIONS}\n{task}\n{text}".encode("utf-8")).hexdigest()
        return self.cache_dir / MODEL / task / f"{digest}.json"

    def _embed(self, texts: list[str], task: str) -> list[list[float]]:
        out: list[list[float] | None] = [None] * len(texts)
        pending: list[int] = []
        for index, text in enumerate(texts):
            path = self._cache_path(task, text)
            if path.is_file():
                out[index] = json.loads(path.read_text(encoding="utf-8"))
            else:
                pending.append(index)
        for start in range(0, len(pending), BATCH):
            batch = pending[start : start + BATCH]
            body = {
                "requests": [
                    {
                        "model": f"models/{MODEL}",
                        "content": {"parts": [{"text": texts[i]}]},
                        "taskType": task,
                        "outputDimensionality": DIMENSIONS,
                    }
                    for i in batch
                ]
            }
            vectors = self._post(body)
            for i, vector in zip(batch, vectors):
                path = self._cache_path(task, texts[i])
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_text(json.dumps(vector), encoding="utf-8")
                out[i] = vector
        return [vector for vector in out if vector is not None]

    def _post(self, body: dict[str, Any]) -> list[list[float]]:
        data = json.dumps(body).encode("utf-8")
        for attempt in range(6):
            request = urllib.request.Request(
                ENDPOINT,
                data=data,
                headers={"Content-Type": "application/json", "x-goog-api-key": self._key()},
                method="POST",
            )
            try:
                with urllib.request.urlopen(request, timeout=120) as response:
                    payload = json.loads(response.read().decode("utf-8"))
                self.calls += 1
                return [item["values"] for item in payload["embeddings"]]
            except urllib.error.HTTPError as error:
                if error.code in {429, 500, 502, 503, 504} and attempt < 5:
                    time.sleep(2**attempt)
                    continue
                detail = error.read().decode("utf-8", "replace")[:300]
                raise RuntimeError(f"Gemini embedding request failed ({error.code}): {detail}") from error
        raise RuntimeError("Gemini embedding request failed after retries")

    def ingest(self, raw_material_dir: Path) -> Path:
        root = Path(raw_material_dir)
        self._key()
        self.docs = []
        paths = corpus_paths(root, self.corpus)
        pieces: list[str] = []
        spans: list[tuple[int, int]] = []
        for path in paths:
            parts = chunks(path.read_text(encoding="utf-8"))
            spans.append((len(pieces), len(pieces) + len(parts)))
            pieces.extend(parts)
        vectors = self._embed(pieces, "RETRIEVAL_DOCUMENT")
        for path, (start, end) in zip(paths, spans):
            self.docs.append((path, vectors[start:end]))
        return root

    def retrieve(self, query: str, k: int) -> dict[str, Any]:
        query_vector = self._embed([query], "RETRIEVAL_QUERY")[0]
        scored = [
            (max(_cosine(query_vector, vector) for vector in vectors), path)
            for path, vectors in self.docs
        ]
        scored.sort(key=lambda item: (-item[0], item[1].stem))
        records = [record(path, self.corpus, score) for score, path in scored[:k]]
        return {"records": records, "plan_context": None}
