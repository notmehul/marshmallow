#!/usr/bin/env python3
"""Mem0 (open source) adapter: LLM fact extraction over raw artifacts, vector search at query time.

Runs Mem0 the way its users run it: ``Memory.add(text, infer=True)`` extracts
memories with an LLM and dedupes against what is stored; ``Memory.search``
returns the extracted memories, not the source files. The retrieved "text" is
therefore Mem0's own paraphrase of the facts, which is what an agent would read.

Configured entirely on Gemini so one key covers extraction and embedding:
gemini-2.5-flash for extraction, gemini-embedding-001 (768d) for vectors, a
local on-disk Qdrant under EVAL_EMBED_CACHE. Needs ``mem0ai`` and
GOOGLE_API_KEY. The store is reused when it already holds memories for this
corpus, so reruns do not re-extract.
"""

from __future__ import annotations

import os
import time
from pathlib import Path
from typing import Any

from base import Adapter
from corpus import corpus_paths

USER = "eval"
LLM_MODEL = "gemini-2.5-flash"
EMBED_MODEL = "models/gemini-embedding-001"
DIMENSIONS = 768


class Mem0Adapter(Adapter):
    name = "mem0"

    def __init__(self) -> None:
        self.memory: Any = None
        self.corpus = "raw"

    def _open(self, store_dir: Path) -> Any:
        if not os.environ.get("GOOGLE_API_KEY"):
            raise RuntimeError("the mem0 adapter needs GOOGLE_API_KEY in the environment")
        try:
            from mem0 import Memory
        except ImportError as error:  # pragma: no cover - environment-dependent
            raise RuntimeError("the mem0 adapter needs the optional mem0ai package: uv pip install mem0ai") from error
        os.environ.setdefault("MEM0_TELEMETRY", "false")
        store_dir.mkdir(parents=True, exist_ok=True)
        config = {
            "llm": {"provider": "gemini", "config": {"model": LLM_MODEL, "temperature": 0.0, "max_tokens": 4000}},
            "embedder": {"provider": "gemini", "config": {"model": EMBED_MODEL, "embedding_dims": DIMENSIONS}},
            "vector_store": {
                "provider": "qdrant",
                "config": {
                    "collection_name": "eval",
                    "path": str(store_dir / "qdrant"),
                    "embedding_model_dims": DIMENSIONS,
                    "on_disk": True,
                },
            },
            "history_db_path": str(store_dir / "history.db"),
        }
        return Memory.from_config(config)

    def ingest(self, raw_material_dir: Path) -> Path:
        root = Path(raw_material_dir)
        cache = Path(os.environ.get("EVAL_EMBED_CACHE", Path(__file__).resolve().parent.parent / "cache"))
        store_dir = cache / "mem0" / root.resolve().name
        self.memory = self._open(store_dir)
        existing = self.memory.get_all(filters={"user_id": USER})
        if existing.get("results"):
            return root
        for path in corpus_paths(root, self.corpus):
            text = path.read_text(encoding="utf-8")
            for attempt in range(6):
                try:
                    self.memory.add(text, user_id=USER, metadata={"source": path.stem}, infer=True)
                    break
                except Exception as error:  # noqa: BLE001 - provider rate limits surface as generic errors
                    if attempt == 5:
                        raise
                    time.sleep(5 * 2**attempt)
        return root

    def retrieve(self, query: str, k: int) -> dict[str, Any]:
        if self.memory is None:
            raise RuntimeError("ingest() must run before retrieve()")
        result = self.memory.search(query, top_k=k, filters={"user_id": USER}, threshold=0.0)
        records = [
            {
                "id": str(item.get("id", "")),
                "kind": "memory",
                "path": str((item.get("metadata") or {}).get("source", "")),
                "score": float(item.get("score") or 0.0),
                "text": str(item.get("memory", "")),
            }
            for item in result.get("results", [])
        ]
        return {"records": records, "plan_context": None}
