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
from scoring import fact_in_text, normalize, score_negative, score_plan_activation, score_query  # noqa: E402


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
        for key in ("direct", "paraphrase", "paraphrase_delta", "negatives", "plan_activation", "mean_wall_ms"):
            self.assertIn(key, aggregate)

    def test_known_answer_queries_score_nontrivially(self) -> None:
        direct = self.report["aggregate"]["direct"]
        self.assertGreaterEqual(direct["recall_at_k"], 0.8)
        self.assertGreaterEqual(direct["mrr"], 0.8)
        self.assertGreater(direct["precision_at_k"], 0.0)
        paraphrase = self.report["aggregate"]["paraphrase"]
        self.assertGreaterEqual(paraphrase["recall_at_k"], 0.8)

    def test_per_query_rows_carry_metrics_and_timing(self) -> None:
        rows = {row["id"]: row for row in self.report["queries"]}
        self.assertEqual(8, len(rows))
        direct_rows = [row for row in rows.values() if row["type"] == "direct"]
        self.assertEqual(6, len(direct_rows))
        for row in direct_rows:
            self.assertGreaterEqual(row["wall_ms"], 0.0)
            self.assertIn("direct", row)
            self.assertIn("paraphrase", row)
            self.assertGreater(row["direct"]["recall_at_k"], 0.0)
        self.assertEqual(1.0, rows["q1-firmware-owner"]["expected_node_recall"])

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
