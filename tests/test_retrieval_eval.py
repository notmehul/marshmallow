from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
EVAL_DIR = ROOT / "evals" / "retrieval-quality"
FIXTURE = EVAL_DIR / "fixture"
RUNNER = EVAL_DIR / "run_eval.py"
sys.path.insert(0, str(ROOT / "scripts"))
sys.path.insert(0, str(EVAL_DIR))
sys.path.insert(0, str(EVAL_DIR / "adapters"))

from marshmallow_adapter import MarshmallowAdapter  # noqa: E402
from recall import recall_context  # noqa: E402
from run_eval import compare_to_baseline  # noqa: E402
from base import load_adapter  # noqa: E402
from corpus import chunks  # noqa: E402
from run_eval import run  # noqa: E402
from scoring import (  # noqa: E402
    estimate_tokens,
    fact_in_text,
    fit_budget,
    normalize,
    score_negative,
    score_nodes,
    score_plan_activation,
    score_query,
)


def fact(claim: str, *aliases: str) -> dict:
    return {"claim": claim, "aliases": list(aliases)}


def record(text: str, score: int = 1, record_id: str = "r") -> dict:
    return {"id": record_id, "kind": "graph", "path": "", "score": score, "text": text}


class NormalizationTests(unittest.TestCase):
    def test_normalize_lowercases_and_collapses_whitespace(self) -> None:
        self.assertEqual("tomas riel owns", normalize("  Tomas\t Riel\n\nOWNS "))

    def test_alias_matches_across_case_and_whitespace(self) -> None:
        self.assertTrue(fact_in_text(fact("owner", "tomas riel"), "TOMAS\n riel owns firmware"))

    def test_hyphenated_alias_does_not_match_spaced_text(self) -> None:
        # Normalization collapses whitespace only; punctuation is literal.
        self.assertFalse(fact_in_text(fact("pricing", "per-greenhouse"), "priced per greenhouse"))
        self.assertTrue(fact_in_text(fact("pricing", "per greenhouse"), "priced per\ngreenhouse"))

    def test_blank_or_missing_aliases_never_match(self) -> None:
        self.assertFalse(fact_in_text(fact("x", "   "), "anything at all"))
        self.assertFalse(fact_in_text({"claim": "x", "aliases": []}, "anything at all"))


class ScoreQueryTests(unittest.TestCase):
    def test_hand_computed_recall_precision_mrr(self) -> None:
        facts = [fact("fact a", "alpha"), fact("fact b", "beta")]
        records = [record("nothing here"), record("alpha content"), record("alpha again")]
        result = score_query(facts, records, k=3)
        self.assertEqual(0.5, result["recall_at_k"])
        self.assertAlmostEqual(2 / 3, result["precision_at_k"])
        self.assertEqual(0.5, result["mrr"])
        self.assertEqual(["fact a"], result["facts_found"])
        self.assertEqual(["fact b"], result["facts_missed"])

    def test_first_record_hit_gives_mrr_one(self) -> None:
        result = score_query([fact("a", "alpha")], [record("alpha"), record("junk")], k=2)
        self.assertEqual(1.0, result["mrr"])
        self.assertEqual(1.0, result["recall_at_k"])
        self.assertEqual(0.5, result["precision_at_k"])

    def test_k_truncates_before_scoring(self) -> None:
        records = [record("junk"), record("junk"), record("junk"), record("alpha")]
        result = score_query([fact("a", "alpha")], records, k=3)
        self.assertEqual(0.0, result["recall_at_k"])
        self.assertEqual(0.0, result["mrr"])
        self.assertEqual(0.0, result["precision_at_k"])

    def test_empty_retrieval_scores_zero(self) -> None:
        result = score_query([fact("a", "alpha")], [], k=5)
        self.assertEqual(0.0, result["recall_at_k"])
        self.assertEqual(0.0, result["precision_at_k"])
        self.assertEqual(0.0, result["mrr"])

    def test_precision_is_over_the_k_budget_not_over_returned_count(self) -> None:
        # One correct record out of a five-slot budget is 0.2, not 1.0.
        result = score_query([fact("a", "alpha")], [record("alpha")], k=5)
        self.assertEqual(0.2, result["precision_at_k"])


class ScoreNodesTests(unittest.TestCase):
    def test_hand_computed_node_metrics(self) -> None:
        records = [
            record("x", record_id="home") | {"kind": "index"},
            record("x", record_id="node-a"),
            record("x", record_id="node-c"),
        ]
        result = score_nodes(["node-a", "node-b"], records, k=3)
        self.assertEqual(0.5, result["recall_at_k"])
        self.assertAlmostEqual(1 / 3, result["precision_at_k"])
        self.assertEqual(0.5, result["mrr"])
        self.assertEqual(["node-a"], result["nodes_found"])
        self.assertEqual(["node-b"], result["nodes_missed"])

    def test_non_graph_record_with_matching_id_does_not_count(self) -> None:
        records = [record("x", record_id="node-a") | {"kind": "recall-packet"}]
        result = score_nodes(["node-a"], records, k=1)
        self.assertEqual(0.0, result["recall_at_k"])
        self.assertEqual(0.0, result["mrr"])

    def test_k_truncates_and_empty_expected_scores_zero(self) -> None:
        records = [record("x", record_id="junk"), record("x", record_id="node-a")]
        self.assertEqual(0.0, score_nodes(["node-a"], records, k=1)["recall_at_k"])
        self.assertEqual(0.0, score_nodes([], records, k=2)["recall_at_k"])


class BudgetTests(unittest.TestCase):
    def test_estimate_tokens_is_about_four_chars_per_token(self) -> None:
        self.assertEqual(0, estimate_tokens("   "))
        self.assertEqual(3, estimate_tokens("twelve chars"))

    def test_fit_budget_keeps_whole_records_in_rank_order_until_one_does_not_fit(self) -> None:
        records = [record("a" * 40, record_id="r1"), record("b" * 40, record_id="r2"), record("c" * 4, record_id="r3")]
        kept = fit_budget(records, budget_tokens=20)
        # r1 (10 tokens) and r2 (10 tokens) fit; r3 would fit but comes after the cut.
        self.assertEqual(["r1", "r2"], [item["id"] for item in kept])
        self.assertEqual([], fit_budget(records, budget_tokens=5))

    def test_chunks_split_long_files_and_never_return_empty(self) -> None:
        text = "para one words\n\n" + " ".join(["w"] * 400) + "\n\npara three"
        parts = chunks(text, max_words=180)
        self.assertGreaterEqual(len(parts), 3)
        self.assertTrue(all(len(part.split()) <= 180 for part in parts))
        self.assertEqual(1, len(chunks("   ")))

    def test_budget_mode_scores_what_fits_and_reports_included_tokens(self) -> None:
        report = run(FIXTURE, FIXTURE / "queries.jsonl", "bm25", k=10, budget_tokens=600)
        self.assertEqual(600, report["budget_tokens"])
        direct_rows = [row for row in report["queries"] if row["type"] == "direct"]
        for row in direct_rows:
            self.assertLessEqual(row["included_tokens"], 600)
            self.assertLessEqual(len(row["retrieved_ids"]), 10)
        # A generous budget must never score below a tight one on recall.
        wide = run(FIXTURE, FIXTURE / "queries.jsonl", "bm25", k=10, budget_tokens=6000)
        self.assertGreaterEqual(
            wide["aggregate"]["node"]["direct"]["recall_at_k"],
            report["aggregate"]["node"]["direct"]["recall_at_k"],
        )


class NegativeScoringTests(unittest.TestCase):
    def test_empty_retrieval_is_disciplined(self) -> None:
        self.assertEqual({"returned": 0, "top_score": 0.0}, score_negative([]))

    def test_junk_retrieval_reports_count_and_top_score(self) -> None:
        result = score_negative([record("junk", score=7), record("more junk", score=3)])
        self.assertEqual({"returned": 2, "top_score": 7.0}, result)


class PlanActivationTests(unittest.TestCase):
    def test_missing_plan_context_returns_none(self) -> None:
        self.assertIsNone(score_plan_activation(None, "plan-a"))

    def test_correct_selection(self) -> None:
        context = {"state": "selected", "selected_id": "plan-a", "candidates": [{"id": "plan-a"}]}
        result = score_plan_activation(context, "plan-a")
        self.assertTrue(result["correct_selection"])
        self.assertFalse(result["false_activation"])
        self.assertFalse(result["lineage_violation"])

    def test_selection_with_no_expected_plan_is_false_activation(self) -> None:
        context = {"state": "selected", "selected_id": "plan-a", "candidates": [{"id": "plan-a"}]}
        result = score_plan_activation(context, None)
        self.assertTrue(result["false_activation"])
        self.assertFalse(result["correct_selection"])

    def test_wrong_plan_selected_is_false_activation(self) -> None:
        context = {"state": "selected", "selected_id": "plan-b", "candidates": [{"id": "plan-b"}]}
        result = score_plan_activation(context, "plan-a")
        self.assertFalse(result["correct_selection"])
        self.assertTrue(result["false_activation"])

    def test_candidate_surfaced_on_ambiguity(self) -> None:
        context = {
            "state": "candidates",
            "selected_id": None,
            "candidates": [{"id": "plan-a"}, {"id": "plan-b"}],
        }
        result = score_plan_activation(context, "plan-a")
        self.assertTrue(result["candidate_surfaced"])
        self.assertFalse(result["false_activation"])

    def test_lineage_gate_flags_drifted_and_inactive_selection(self) -> None:
        context = {"state": "selected", "selected_id": "plan-a", "candidates": [{"id": "plan-a"}]}
        for lineage in ("drifted", "inactive"):
            result = score_plan_activation(context, "plan-a", {"plan-a": lineage})
            self.assertTrue(result["lineage_violation"], lineage)
        result = score_plan_activation(context, "plan-a", {"plan-a": "active"})
        self.assertFalse(result["lineage_violation"])


class BaselineComparisonTests(unittest.TestCase):
    AGGREGATE = {
        "node": {
            "labeled": 40,
            "direct": {"recall_at_k": 0.92, "precision_at_k": 0.4, "mrr": 0.87},
            "paraphrase": {"recall_at_k": 0.59, "precision_at_k": 0.25, "mrr": 0.63},
            "paraphrase_delta": {"recall_at_k": 0.33, "precision_at_k": 0.15, "mrr": 0.24},
        },
        "fact_containment": {
            "labeled": 40,
            "direct": {"recall_at_k": 1.0, "precision_at_k": 1.0, "mrr": 1.0},
            "paraphrase": {"recall_at_k": 0.86, "precision_at_k": 0.58, "mrr": 0.85},
            "paraphrase_delta": {"recall_at_k": 0.14, "precision_at_k": 0.32, "mrr": 0.15},
        },
        "negatives": {
            "count": 10,
            "zero_result_fraction": 0.5,
            "junk_mean_top_score": 40.4,
            "true_positive_mean_top_score": 55.8,
        },
        "plan_activation": "unavailable",
        "mean_wall_ms": 23.1,
    }

    def test_identical_aggregates_pass(self) -> None:
        self.assertEqual(compare_to_baseline(self.AGGREGATE, self.AGGREGATE, 0.02), [])

    def test_drift_within_tolerance_passes(self) -> None:
        current = json.loads(json.dumps(self.AGGREGATE))
        current["node"]["direct"]["precision_at_k"] = 0.385
        self.assertEqual(compare_to_baseline(current, self.AGGREGATE, 0.02), [])

    def test_drift_beyond_tolerance_is_a_breach(self) -> None:
        current = json.loads(json.dumps(self.AGGREGATE))
        current["node"]["paraphrase"]["mrr"] = 0.58
        breaches = compare_to_baseline(current, self.AGGREGATE, 0.02)
        self.assertEqual(len(breaches), 1)
        self.assertIn("node.paraphrase.mrr", breaches[0])

    def test_missing_metric_is_a_breach(self) -> None:
        current = json.loads(json.dumps(self.AGGREGATE))
        del current["node"]["direct"]["mrr"]
        breaches = compare_to_baseline(current, self.AGGREGATE, 0.02)
        self.assertEqual(len(breaches), 1)
        self.assertIn("node.direct.mrr", breaches[0])

    def test_machine_dependent_leaves_are_ignored(self) -> None:
        current = json.loads(json.dumps(self.AGGREGATE))
        current["mean_wall_ms"] = 900.0
        current["negatives"]["junk_mean_top_score"] = 99.0
        current["negatives"]["true_positive_mean_top_score"] = 10.0
        self.assertEqual(compare_to_baseline(current, self.AGGREGATE, 0.02), [])

    def test_fact_containment_is_diagnostic_not_guarded(self) -> None:
        current = json.loads(json.dumps(self.AGGREGATE))
        current["fact_containment"]["direct"]["mrr"] = 0.1
        self.assertEqual(compare_to_baseline(current, self.AGGREGATE, 0.02), [])

    def test_pinned_baseline_file_matches_guarded_shape(self) -> None:
        baseline = json.loads((EVAL_DIR / "baseline.json").read_text(encoding="utf-8"))
        self.assertEqual(compare_to_baseline(baseline["aggregate"], baseline["aggregate"], 0.0), [])
        for section in ("node", "fact_containment", "negatives"):
            self.assertIn(section, baseline["aggregate"])
        for view in ("direct", "paraphrase", "paraphrase_delta"):
            self.assertIn(view, baseline["aggregate"]["node"])


class MarshmallowAdapterTests(unittest.TestCase):
    def test_retrieve_wraps_the_cli_recall_and_attaches_file_text(self) -> None:
        adapter = MarshmallowAdapter()
        adapter.ingest(FIXTURE)
        output = adapter.retrieve("kestrel micro humidity sensors", 5)
        expected = recall_context(FIXTURE, "kestrel micro humidity sensors", limit=5)
        self.assertEqual(
            [result["id"] for result in expected],
            [item["id"] for item in output["records"]],
        )
        self.assertIn("plan_context", output)
        for item in output["records"]:
            self.assertTrue(item["text"].startswith("---\n"))
            self.assertIn(f"id: {item['id']}", item["text"])


class BaselineAdapterTests(unittest.TestCase):
    def test_random_adapter_is_deterministic_and_ignores_the_query(self) -> None:
        adapter = load_adapter("random")
        adapter.ingest(FIXTURE)
        first = [item["id"] for item in adapter.retrieve("kestrel micro humidity sensors", 3)["records"]]
        again = [item["id"] for item in adapter.retrieve("kestrel micro humidity sensors", 3)["records"]]
        self.assertEqual(first, again)
        self.assertEqual(3, len(first))
        self.assertTrue(all(item["kind"] == "graph" for item in adapter.retrieve("anything", 2)["records"]))

    def test_bm25_ranks_the_answer_node_first_on_a_known_query(self) -> None:
        adapter = load_adapter("bm25")
        adapter.ingest(FIXTURE)
        output = adapter.retrieve("kestrel micro humidity sensors", 3)
        self.assertEqual("kestrel-sensor-switch", output["records"][0]["id"])
        self.assertTrue(output["records"][0]["text"].startswith("---\n"))
        self.assertEqual([], adapter.retrieve("zzqx", 3)["records"])

    def test_raw_corpus_adapters_need_a_raw_directory(self) -> None:
        with self.assertRaises(FileNotFoundError):
            load_adapter("bm25-raw").ingest(FIXTURE)

    def test_embed_adapter_is_optional_and_registered(self) -> None:
        adapter = load_adapter("embed-graph")
        self.assertEqual("embed-graph", adapter.name)
        try:
            import fastembed  # noqa: F401
        except ImportError:
            with self.assertRaises(RuntimeError):
                adapter.ingest(FIXTURE)
            return
        adapter.ingest(FIXTURE)
        output = adapter.retrieve("kestrel micro humidity sensors", 3)
        self.assertEqual("kestrel-sensor-switch", output["records"][0]["id"])

    def test_hosted_adapters_register_and_fail_clearly_without_credentials(self) -> None:
        import os

        saved = {key: os.environ.pop(key, None) for key in ("GEMINI_API_KEY", "GOOGLE_API_KEY", "GBRAIN_HOME")}
        try:
            for name in ("gemini-graph", "gemini-raw", "mem0", "gbrain", "gbrain-expand"):
                adapter = load_adapter(name)
                self.assertEqual(name, adapter.name)
            with self.assertRaisesRegex(RuntimeError, "GEMINI_API_KEY"):
                load_adapter("gemini-graph").ingest(FIXTURE)
            with self.assertRaisesRegex(RuntimeError, "GOOGLE_API_KEY|mem0ai"):
                load_adapter("mem0").ingest(FIXTURE)
            with self.assertRaisesRegex(RuntimeError, "gbrain|GBRAIN_HOME"):
                load_adapter("gbrain").ingest(EVAL_DIR / "seed")
        finally:
            for key, value in saved.items():
                if value is not None:
                    os.environ[key] = value

    def test_unknown_adapter_names_are_rejected(self) -> None:
        with self.assertRaises(ValueError):
            load_adapter("nope")


class EndToEndTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.temp = tempfile.TemporaryDirectory()
        report_path = Path(cls.temp.name) / "report.json"
        result = subprocess.run(
            [
                sys.executable,
                str(RUNNER),
                "--workspace",
                str(FIXTURE),
                "--queries",
                str(FIXTURE / "queries.jsonl"),
                "--json",
                str(report_path),
            ],
            cwd=ROOT,
            check=False,
            text=True,
            capture_output=True,
        )
        assert result.returncode == 0, result.stdout + result.stderr
        cls.report = json.loads(report_path.read_text(encoding="utf-8"))

    @classmethod
    def tearDownClass(cls) -> None:
        cls.temp.cleanup()

    def test_report_shape_and_identifiers(self) -> None:
        report = self.report
        for key in ("adapter", "dataset", "tier", "workspace", "k", "query_count", "queries", "aggregate"):
            self.assertIn(key, report)
        self.assertEqual("marshmallow", report["adapter"])
        self.assertEqual("fixture", report["tier"])
        self.assertEqual(8, report["query_count"])
        aggregate = report["aggregate"]
        for key in ("node", "fact_containment", "negatives", "plan_activation", "mean_wall_ms"):
            self.assertIn(key, aggregate)
        for view in ("direct", "paraphrase", "paraphrase_delta"):
            self.assertIn(view, aggregate["node"])
            self.assertIn(view, aggregate["fact_containment"])

    def test_known_answer_queries_score_nontrivially(self) -> None:
        node = self.report["aggregate"]["node"]
        self.assertEqual(6, node["labeled"])
        self.assertGreaterEqual(node["direct"]["recall_at_k"], 0.8)
        self.assertGreaterEqual(node["direct"]["mrr"], 0.8)
        self.assertGreater(node["direct"]["precision_at_k"], 0.0)
        self.assertGreaterEqual(node["paraphrase"]["recall_at_k"], 0.6)
        fact = self.report["aggregate"]["fact_containment"]
        self.assertGreaterEqual(fact["direct"]["recall_at_k"], 0.8)

    def test_per_query_rows_carry_metrics_and_timing(self) -> None:
        rows = {row["id"]: row for row in self.report["queries"]}
        self.assertEqual(8, len(rows))
        direct_rows = [row for row in rows.values() if row["type"] == "direct"]
        self.assertEqual(6, len(direct_rows))
        for row in direct_rows:
            self.assertGreaterEqual(row["wall_ms"], 0.0)
            self.assertIn("direct", row["fact"])
            self.assertIn("paraphrase", row["fact"])
            self.assertIn("direct", row["node"])
            self.assertGreater(row["fact"]["direct"]["recall_at_k"], 0.0)
        self.assertEqual(1.0, rows["q1-firmware-owner"]["node"]["direct"]["recall_at_k"])

    def test_negatives_split_between_zero_results_and_scored_junk(self) -> None:
        rows = {row["id"]: row for row in self.report["queries"]}
        self.assertEqual(0, rows["q8-payroll-ledger"]["negative"]["returned"])
        self.assertGreater(rows["q7-office-lease"]["negative"]["returned"], 0)
        negatives = self.report["aggregate"]["negatives"]
        self.assertEqual(2, negatives["count"])
        self.assertEqual(0.5, negatives["zero_result_fraction"])
        # Junk on negatives should score below real answers on direct queries.
        self.assertLess(negatives["junk_mean_top_score"], negatives["true_positive_mean_top_score"])

    def test_plan_activation_degrades_gracefully_without_plan_fields(self) -> None:
        self.assertEqual("unavailable", self.report["aggregate"]["plan_activation"])


if __name__ == "__main__":
    unittest.main()
