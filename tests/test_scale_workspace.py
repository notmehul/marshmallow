from __future__ import annotations

import re
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
EVAL_DIR = ROOT / "evals" / "retrieval-quality"
SEED = EVAL_DIR / "seed"
sys.path.insert(0, str(ROOT / "scripts"))
sys.path.insert(0, str(EVAL_DIR))

from markdown_graph import graph_quality_warnings, validate_workspace  # noqa: E402
from scale_workspace import CLONE_DIRS, build_tier, main, normalize, planted_fact_anchors  # noqa: E402

TOKEN = re.compile(r"[a-z0-9]+")


def tree_bytes(root: Path) -> dict[str, bytes]:
    return {
        str(path.relative_to(root)): path.read_bytes()
        for path in sorted(root.rglob("*.md"))
    }


def vocabulary(paths: list[Path]) -> set[str]:
    tokens: set[str] = set()
    for path in paths:
        tokens.update(TOKEN.findall(path.read_text(encoding="utf-8").lower()))
    return tokens


def seed_relative_paths() -> set[str]:
    paths = {"runtime.md"}
    for directory in CLONE_DIRS:
        paths.update(f"{directory}/{path.name}" for path in (SEED / directory).glob("*.md"))
    return paths


class ScaledTierTests(unittest.TestCase):
    """Property tests on one generated 200-node tier (kept small for runtime)."""

    @classmethod
    def setUpClass(cls) -> None:
        cls.temp = tempfile.TemporaryDirectory()
        cls.tier = Path(cls.temp.name) / "tier200"
        # Through main() so the CLI contract (flags, exit code) is covered too.
        exit_code = main(
            [
                "--seed-workspace", str(SEED),
                "--target-nodes", "200",
                "--rng-seed", "7",
                "--out", str(cls.tier),
            ]
        )
        assert exit_code == 0

    @classmethod
    def tearDownClass(cls) -> None:
        cls.temp.cleanup()

    def clone_paths(self) -> list[Path]:
        seed_paths = seed_relative_paths()
        return [
            path
            for path in sorted(self.tier.rglob("*.md"))
            if str(path.relative_to(self.tier)) not in seed_paths
        ]

    def test_tier_passes_doctor_with_zero_errors_and_zero_warnings(self) -> None:
        self.assertEqual([], validate_workspace(self.tier))
        self.assertEqual([], graph_quality_warnings(self.tier))

    def test_node_count_matches_target(self) -> None:
        self.assertEqual(200, len(list((self.tier / "graph").glob("*.md"))))

    def test_original_seed_files_are_byte_identical(self) -> None:
        for relative in sorted(seed_relative_paths()):
            with self.subTest(file=relative):
                self.assertEqual(
                    (SEED / relative).read_bytes(),
                    (self.tier / relative).read_bytes(),
                )

    def test_no_planted_fact_anchor_appears_in_any_clone(self) -> None:
        anchors = [normalize(anchor) for anchor in planted_fact_anchors(SEED / "bible.md")]
        self.assertGreaterEqual(len(anchors), 96)  # 48 facts, multiple anchors each
        clones = self.clone_paths()
        self.assertGreater(len(clones), 0)
        for path in clones:
            haystack = normalize(path.read_text(encoding="utf-8"))
            leaked = [anchor for anchor in anchors if anchor in haystack]
            self.assertEqual([], leaked, f"anchors leaked into {path.name}")

    def test_clone_vocabulary_measurably_overlaps_seed_vocabulary(self) -> None:
        seed_vocab = vocabulary(sorted((SEED / "graph").glob("*.md")))
        clone_vocab = vocabulary(
            [path for path in self.clone_paths() if path.parent.name == "graph"]
        )
        overlap = len(seed_vocab & clone_vocab) / len(seed_vocab)
        # Near-miss distractors: most structural vocabulary is shared, but
        # renames and anchor mutations mean the overlap is never total.
        self.assertGreaterEqual(overlap, 0.7)
        self.assertLess(overlap, 1.0)

    def test_same_rng_seed_reproduces_bytes_and_different_seed_does_not(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            rerun = Path(temp) / "rerun"
            other = Path(temp) / "other"
            build_tier(SEED, 200, 7, rerun)
            build_tier(SEED, 200, 11, other)
            baseline = tree_bytes(self.tier)
            self.assertEqual(baseline, tree_bytes(rerun))
            self.assertNotEqual(baseline, tree_bytes(other))

    def test_rejects_targets_that_are_not_whole_universes(self) -> None:
        for target in (100, 150, 250):
            with self.subTest(target=target), tempfile.TemporaryDirectory() as temp:
                with self.assertRaises(ValueError):
                    build_tier(SEED, target, 7, Path(temp) / "tier")


if __name__ == "__main__":
    unittest.main()
