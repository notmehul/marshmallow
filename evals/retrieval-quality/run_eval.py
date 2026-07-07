#!/usr/bin/env python3
"""Run one workspace tier through a retrieval adapter, score it, emit a report."""

from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path
from typing import Any

EVAL_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(EVAL_DIR))
sys.path.insert(0, str(EVAL_DIR / "adapters"))

from base import load_adapter  # noqa: E402
from scoring import mean, score_negative, score_plan_activation, score_query  # noqa: E402

QUERY_TYPES = ("direct", "negative")


def load_queries(path: Path) -> list[dict[str, Any]]:
    queries: list[dict[str, Any]] = []
    for number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
        if not line.strip():
            continue
        try:
            query = json.loads(line)
        except json.JSONDecodeError as error:
            raise ValueError(f"{path}:{number}: invalid JSON: {error}") from error
        for field in ("id", "text", "type"):
            if not str(query.get(field, "")).strip():
                raise ValueError(f"{path}:{number}: query is missing {field!r}")
        if query["type"] not in QUERY_TYPES:
            raise ValueError(f"{path}:{number}: type must be one of {QUERY_TYPES}")
        facts = query.get("facts", [])
        # Label hygiene: known-answer queries carry facts, negatives never do.
        if query["type"] == "direct" and not facts:
            raise ValueError(f"{path}:{number}: direct query needs at least one fact")
        if query["type"] == "negative" and facts:
            raise ValueError(f"{path}:{number}: negative query must not carry facts")
        queries.append(query)
    if not queries:
        raise ValueError(f"{path}: no queries found")
    return queries


def timed_retrieve(adapter: Any, query_text: str, k: int) -> tuple[dict[str, Any], float]:
    started = time.perf_counter()
    output = adapter.retrieve(query_text, k)
    return output, (time.perf_counter() - started) * 1000.0


def evaluate_query(adapter: Any, query: dict[str, Any], k: int) -> dict[str, Any]:
    output, wall_ms = timed_retrieve(adapter, query["text"], k)
    records = output["records"]
    row: dict[str, Any] = {
        "id": query["id"],
        "type": query["type"],
        "wall_ms": round(wall_ms, 3),
        "retrieved_ids": [record["id"] for record in records],
        "top_score": float(records[0].get("score", 0)) if records else 0.0,
    }
    expectations = query.get("marshmallow", {})
    if query["type"] == "negative":
        row["negative"] = score_negative(records)
    else:
        row["direct"] = score_query(query["facts"], records, k)
        paraphrase = str(query.get("paraphrase", "")).strip()
        if paraphrase:
            paraphrase_output, _ = timed_retrieve(adapter, paraphrase, k)
            row["paraphrase"] = score_query(query["facts"], paraphrase_output["records"], k)
        expected_nodes = expectations.get("expected_node_ids", [])
        if expected_nodes:
            hits = [node_id for node_id in expected_nodes if node_id in row["retrieved_ids"]]
            row["expected_node_recall"] = len(hits) / len(expected_nodes)
    plan_row = score_plan_activation(output.get("plan_context"), expectations.get("expected_plan"))
    if plan_row is not None:
        row["plan"] = plan_row
    return row


def rounded(value: float | None) -> float | None:
    return None if value is None else round(value, 4)


def metric_means(rows: list[dict[str, Any]]) -> dict[str, float | None]:
    return {
        name: rounded(mean([row[name] for row in rows]))
        for name in ("recall_at_k", "precision_at_k", "mrr")
    }


def aggregate_rows(rows: list[dict[str, Any]]) -> dict[str, Any]:
    direct_rows = [row["direct"] for row in rows if "direct" in row]
    paired = [(row["direct"], row["paraphrase"]) for row in rows if "paraphrase" in row]
    negative_rows = [row["negative"] for row in rows if "negative" in row]
    plan_rows = [row["plan"] for row in rows if "plan" in row]

    # Paraphrase delta is paired (direct minus paraphrase per query), so
    # queries without a paraphrase variant do not skew the gap.
    delta = {
        name: rounded(mean([direct[name] - paraphrase[name] for direct, paraphrase in paired]))
        for name in ("recall_at_k", "precision_at_k", "mrr")
    }

    junk_scores = [row["top_score"] for row in negative_rows if row["returned"] > 0]
    true_positive_scores = [
        row["top_score"] for row in rows if "direct" in row and row["retrieved_ids"]
    ]
    negatives = {
        "count": len(negative_rows),
        "zero_result_fraction": rounded(
            mean([1.0 if row["returned"] == 0 else 0.0 for row in negative_rows])
        ),
        "junk_mean_top_score": rounded(mean(junk_scores)),
        "true_positive_mean_top_score": rounded(mean(true_positive_scores)),
    }

    if plan_rows:
        plan_activation: Any = {
            "scored": len(plan_rows),
            "correct_selection_rate": rounded(
                mean([1.0 if row["correct_selection"] else 0.0 for row in plan_rows])
            ),
            "false_activation_rate": rounded(
                mean([1.0 if row["false_activation"] else 0.0 for row in plan_rows])
            ),
            "candidate_surfaced_rate": rounded(
                mean([1.0 if row["candidate_surfaced"] else 0.0 for row in plan_rows])
            ),
            "lineage_violations": sum(1 for row in plan_rows if row["lineage_violation"]),
        }
    else:
        # This branch's recall emits no plan fields; report the gap instead of
        # failing so the same runner works before and after plan-centered recall.
        plan_activation = "unavailable"

    return {
        "direct": metric_means(direct_rows),
        "paraphrase": metric_means([paraphrase for _, paraphrase in paired]),
        "paraphrase_delta": delta,
        "negatives": negatives,
        "plan_activation": plan_activation,
        "mean_wall_ms": rounded(mean([row["wall_ms"] for row in rows])),
    }


def run(workspace: Path, queries_path: Path, adapter_name: str, k: int) -> dict[str, Any]:
    adapter = load_adapter(adapter_name)
    adapter.ingest(workspace)
    rows = [evaluate_query(adapter, query, k) for query in load_queries(queries_path)]
    return {
        "adapter": adapter_name,
        "dataset": str(queries_path),
        "tier": workspace.resolve().name,
        "workspace": str(workspace.resolve()),
        "k": k,
        "query_count": len(rows),
        "queries": rows,
        "aggregate": aggregate_rows(rows),
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Score a workspace tier through a retrieval adapter.")
    parser.add_argument("--workspace", type=Path, required=True, help="Tier directory (a Marshmallow workspace).")
    parser.add_argument("--queries", type=Path, required=True, help="queries.jsonl path.")
    parser.add_argument("--adapter", default="marshmallow", help="Adapter name (default: marshmallow).")
    parser.add_argument("--json", type=Path, default=None, help="Write the report JSON here (default: stdout).")
    parser.add_argument("--k", type=int, default=5, help="Result budget per query (default: 5).")
    args = parser.parse_args(argv)
    if args.k < 1:
        parser.error("--k must be at least 1")

    report = run(args.workspace, args.queries, args.adapter, args.k)
    payload = json.dumps(report, indent=2, sort_keys=True) + "\n"
    if args.json:
        args.json.parent.mkdir(parents=True, exist_ok=True)
        args.json.write_text(payload, encoding="utf-8")
        direct = report["aggregate"]["direct"]
        print(
            f"{report['adapter']} on {report['tier']}: "
            f"recall@{args.k}={direct['recall_at_k']} mrr={direct['mrr']} -> {args.json}"
        )
    else:
        print(payload, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
