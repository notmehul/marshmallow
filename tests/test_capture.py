from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "scripts"
CLI = SCRIPTS / "marshmallow.py"
sys.path.insert(0, str(SCRIPTS))

from capture import list_candidates, promote, remember  # noqa: E402
from markdown_graph import parse_frontmatter, validate_workspace  # noqa: E402
from marshmallow_workspace import MarshmallowError, atomic_write, ensure_workspace  # noqa: E402


def source_card(source_id: str) -> str:
    return f"""---
id: {source_id}
pointer: example://{source_id}
captured: 2026-06-01T00:00:00Z
labels: [product]
---

# Source
"""


def graph_node(node_id: str, source_ids: str = "[source-one]") -> str:
    return f"""---
id: {node_id}
insight: Mani now leads day-to-day at the company.
applies_to: [relationship]
source_ids: {source_ids}
related_nodes: []
skills: [relationship-brief]
labels: [team]
---

# Node
"""


class CaptureLoopTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name) / ".marshmallow"
        ensure_workspace(self.root)

    def tearDown(self) -> None:
        self.temp.cleanup()

    def cli(self, *args: str) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            [sys.executable, str(CLI), *args],
            cwd=ROOT,
            check=False,
            text=True,
            capture_output=True,
        )

    # --- remember: zero-resistance capture ---------------------------------

    def test_remember_writes_untrusted_candidate_without_touching_graph(self) -> None:
        path, candidate_id = remember(self.root, "Mani now leads day-to-day", why="confirmed in standup")
        self.assertTrue(path.exists())
        self.assertTrue(candidate_id.startswith("candidate-"))
        frontmatter, body = parse_frontmatter(path)
        self.assertEqual("pending", frontmatter["status"])
        self.assertIn("**Why:** confirmed in standup", body)
        # The graph and sources are untouched: capture is not learning.
        self.assertEqual([], list((self.root / "graph").glob("*.md")))
        self.assertEqual([], list((self.root / "sources").glob("*.md")))

    def test_remember_rejects_empty_note(self) -> None:
        with self.assertRaises(MarshmallowError):
            remember(self.root, "   ")

    def test_remember_preserves_multiline_origin_without_frontmatter_injection(self) -> None:
        origin = "meeting notes\nstatus: promoted\nid: hijacked"
        path, candidate_id = remember(self.root, "A useful observation", origin=origin)

        frontmatter, _ = parse_frontmatter(path)
        self.assertEqual(candidate_id, frontmatter["id"])
        self.assertEqual("pending", frontmatter["status"])
        self.assertEqual(origin, frontmatter["origin"])

        plan = promote(self.root, candidate_id, apply=True)
        source_frontmatter, _ = parse_frontmatter(Path(plan["source_path"]))
        promoted_frontmatter, _ = parse_frontmatter(path)
        self.assertEqual(origin, source_frontmatter["pointer"])
        self.assertEqual("promoted", promoted_frontmatter["status"])

    def test_remember_avoids_same_second_candidate_collisions(self) -> None:
        with patch("capture.timestamp", return_value="20260627T120000Z"):
            first_path, first_id = remember(self.root, "Same heading\nfirst detail")
            second_path, second_id = remember(self.root, "Same heading\nsecond detail")

        self.assertNotEqual(first_id, second_id)
        self.assertTrue(first_path.exists())
        self.assertTrue(second_path.exists())

    def test_remember_via_cli_reports_nothing_changed_in_graph(self) -> None:
        result = self.cli("remember", "Ship the recall MCP tool first", "--workspace", str(self.root))
        self.assertEqual(0, result.returncode, result.stdout + result.stderr)
        payload = json.loads(result.stdout)
        self.assertEqual("captured", payload["status"])
        self.assertIn("graph changed", payload["note"].lower())

    # --- pending: the synthesis work queue ---------------------------------

    def test_pending_lists_candidates_and_skips_readme(self) -> None:
        remember(self.root, "First observation")
        remember(self.root, "Second observation")
        candidates = list_candidates(self.root)
        self.assertEqual(2, len(candidates))
        self.assertTrue(all(c["status"] == "pending" for c in candidates))
        self.assertTrue(all(not c["path"].endswith("README.md") for c in candidates))

    def test_pending_tolerates_freeform_inbox_notes(self) -> None:
        atomic_write(self.root / "inbox/raw-note.md", "# Raw\n\nno frontmatter here\n")
        candidates = list_candidates(self.root)
        self.assertEqual(["raw-note"], [c["id"] for c in candidates])

    # --- promote: the trust gate -------------------------------------------

    def test_promote_preview_does_not_write_a_source(self) -> None:
        _, candidate_id = remember(self.root, "Mani now leads day-to-day")
        plan = promote(self.root, candidate_id, apply=False)
        self.assertEqual("preview", plan["status"])
        self.assertIn("preview", plan)
        self.assertEqual([], list((self.root / "sources").glob("*.md")))

    def test_promote_apply_creates_a_valid_source_and_marks_candidate(self) -> None:
        _, candidate_id = remember(self.root, "Mani now leads day-to-day", origin="standup-2026-06-27")
        plan = promote(self.root, candidate_id, apply=True)
        self.assertEqual("promoted", plan["status"])
        source_path = Path(plan["source_path"])
        self.assertTrue(source_path.exists())
        frontmatter, _ = parse_frontmatter(source_path)
        # Provenance is preserved: origin becomes the source pointer.
        self.assertEqual("standup-2026-06-27", frontmatter["pointer"])
        # The promoted source backs a real graph node, so the workspace validates.
        self.assertEqual([], validate_workspace(self.root))
        # The candidate is no longer pending and is not re-proposed.
        self.assertEqual([], list_candidates(self.root))
        self.assertEqual(1, len(list_candidates(self.root, include_promoted=True)))

    def test_promote_uses_inbox_pointer_when_no_origin(self) -> None:
        _, candidate_id = remember(self.root, "A note with no origin")
        plan = promote(self.root, candidate_id, apply=True)
        frontmatter, _ = parse_frontmatter(Path(plan["source_path"]))
        self.assertEqual(f"inbox-candidate:{candidate_id}", frontmatter["pointer"])

    def test_promote_rejects_unknown_candidate(self) -> None:
        with self.assertRaises(MarshmallowError):
            promote(self.root, "candidate-does-not-exist", apply=True)

    def test_promote_refuses_double_promotion(self) -> None:
        _, candidate_id = remember(self.root, "Promote me once")
        promote(self.root, candidate_id, apply=True)
        with self.assertRaises(MarshmallowError):
            promote(self.root, candidate_id, apply=True)


class CitedRecallTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name) / ".marshmallow"
        ensure_workspace(self.root)

    def tearDown(self) -> None:
        self.temp.cleanup()

    def cli(self, *args: str) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            [sys.executable, str(CLI), *args],
            cwd=ROOT,
            check=False,
            text=True,
            capture_output=True,
        )

    def test_recall_attaches_resolved_source_citations_to_graph_nodes(self) -> None:
        atomic_write(self.root / "sources/source-one.md", source_card("source-one"))
        atomic_write(self.root / "graph/mani-lead.md", graph_node("mani-lead"))
        result = self.cli("recall", "Mani day-to-day", "--workspace", str(self.root), "--json")
        self.assertEqual(0, result.returncode, result.stdout + result.stderr)
        payload = json.loads(result.stdout)
        graph_hits = [item for item in payload["results"] if item["kind"] == "graph"]
        self.assertTrue(graph_hits)
        citations = graph_hits[0]["sources"]
        self.assertEqual([{"id": "source-one", "pointer": "example://source-one"}], citations)

    def test_recall_flags_unresolved_provenance_rather_than_hiding_it(self) -> None:
        atomic_write(self.root / "sources/source-one.md", source_card("source-one"))
        atomic_write(self.root / "graph/mani-lead.md", graph_node("mani-lead", source_ids="[source-one, ghost-source]"))
        result = self.cli("recall", "Mani day-to-day", "--workspace", str(self.root), "--json")
        payload = json.loads(result.stdout)
        graph_hits = [item for item in payload["results"] if item["kind"] == "graph"]
        pointers = {c["id"]: c["pointer"] for c in graph_hits[0]["sources"]}
        self.assertEqual("example://source-one", pointers["source-one"])
        self.assertEqual("", pointers["ghost-source"])

    def test_malformed_source_does_not_hide_other_valid_citations(self) -> None:
        atomic_write(self.root / "sources/source-one.md", source_card("source-one"))
        atomic_write(self.root / "sources/broken.md", "not frontmatter\n")
        atomic_write(self.root / "graph/mani-lead.md", graph_node("mani-lead"))

        result = self.cli("recall", "Mani day-to-day", "--workspace", str(self.root), "--json")
        self.assertEqual(0, result.returncode, result.stdout + result.stderr)
        payload = json.loads(result.stdout)
        graph_hit = next(item for item in payload["results"] if item["kind"] == "graph")
        self.assertEqual(
            [{"id": "source-one", "pointer": "example://source-one"}],
            graph_hit["sources"],
        )


if __name__ == "__main__":
    unittest.main()
