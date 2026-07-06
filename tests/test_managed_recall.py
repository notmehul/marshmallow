from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

import sys

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "scripts"
sys.path.insert(0, str(SCRIPTS))

from marshmallow_workspace import atomic_write, ensure_workspace  # noqa: E402
from recall import recall_bundle  # noqa: E402
from record_access import get_record  # noqa: E402


def source_card() -> str:
    return """---
id: source-one
pointer: example://source-one
captured: 2026-07-05T00:00:00Z
---

# Source
"""


def graph_node(
    node_id: str,
    insight: str,
    *,
    related_nodes: str = "[]",
    node_type: str = "entity",
    managed: str = "false",
    body: str | None = None,
) -> str:
    return f"""---
id: {node_id}
insight: {insight}
type: {node_type}
source_ids: [source-one]
related_nodes: {related_nodes}
managed: {managed}
status: active
updated: 2026-07-05
---

{body or f'# {node_id}\n'}
"""


class ManagedRecallTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name) / ".marshmallow"
        ensure_workspace(self.root)
        atomic_write(self.root / "sources/source-one.md", source_card())

    def tearDown(self) -> None:
        self.temp.cleanup()

    def write_graph(self, node_id: str, content: str) -> None:
        atomic_write(self.root / "graph" / f"{node_id}.md", content)

    def test_weak_plan_match_does_not_hide_stronger_direct_result(self) -> None:
        self.write_graph(
            "old-plan",
            graph_node(
                "old-plan",
                "Coordinate the old hiring work.",
                related_nodes="[hiring]",
                node_type="plan",
                managed="true",
            ),
        )
        self.write_graph(
            "hiring",
            graph_node("hiring", "The hiring relationship remains warm.", related_nodes="[old-plan]"),
        )
        self.write_graph(
            "cobalt-review",
            graph_node("cobalt-review", "Prepare the quarterly cobalt review with retention evidence."),
        )

        payload = recall_bundle(self.root, "prepare the quarterly cobalt review")

        self.assertEqual("none", payload["plan_context"]["state"])
        self.assertEqual("cobalt-review", payload["results"][0]["id"])

    def test_broad_index_only_credits_the_matching_link_line(self) -> None:
        for node_id in ("alpha-plan", "zeta-plan"):
            self.write_graph(
                node_id,
                graph_node(
                    node_id,
                    f"Coordinate {node_id} work.",
                    node_type="plan",
                    managed="true",
                ),
            )
        atomic_write(
            self.root / "indexes/home.md",
            """---
id: home
title: Portfolio Home
graph_ids: [alpha-plan, zeta-plan]
---

# Home

- [[alpha-plan]] - unrelated launch work.
- [[zeta-plan]] - cobalt launch only.
""",
        )

        payload = recall_bundle(self.root, "cobalt launch")

        self.assertEqual("selected", payload["plan_context"]["state"])
        self.assertEqual("zeta-plan", payload["plan_context"]["selected_id"])
        self.assertEqual("zeta-plan", payload["results"][0]["id"])

    def test_multiple_qualified_plans_are_returned_as_candidates(self) -> None:
        self.write_graph(
            "alpha-plan",
            graph_node(
                "alpha-plan",
                "Coordinate the cobalt launch.",
                node_type="plan",
                managed="true",
            ),
        )
        self.write_graph(
            "beta-plan",
            graph_node(
                "beta-plan",
                "Coordinate the cobalt launch.",
                node_type="plan",
                managed="true",
            ),
        )

        payload = recall_bundle(self.root, "cobalt launch")

        self.assertEqual("candidates", payload["plan_context"]["state"])
        self.assertIsNone(payload["plan_context"]["selected_id"])
        self.assertEqual(
            ["alpha-plan", "beta-plan"],
            [item["id"] for item in payload["plan_context"]["candidates"]],
        )
        self.assertEqual("plan-candidate", payload["results"][0]["role"])

    def test_selected_plan_keeps_strong_direct_matches_and_adds_context(self) -> None:
        self.write_graph(
            "launch-plan",
            graph_node(
                "launch-plan",
                "Coordinate the cobalt launch.",
                related_nodes="[launch-project, partner]",
                node_type="plan",
                managed="true",
            ),
        )
        self.write_graph(
            "launch-project",
            graph_node(
                "launch-project",
                "The cobalt launch review is ready.",
                related_nodes="[launch-plan]",
            ),
        )
        self.write_graph(
            "partner",
            graph_node("partner", "The partner prefers a concise note.", related_nodes="[launch-plan]"),
        )
        self.write_graph(
            "direct-evidence",
            graph_node("direct-evidence", "Cobalt launch evidence belongs in the review."),
        )

        payload = recall_bundle(self.root, "cobalt launch review", limit=6)
        ids = [item["id"] for item in payload["results"]]

        self.assertEqual("launch-plan", ids[0])
        self.assertIn("direct-evidence", ids)
        self.assertIn("partner", ids)
        partner = next(item for item in payload["results"] if item["id"] == "partner")
        self.assertEqual("connected-to-plan", partner["role"])

    def test_direct_plan_candidate_does_not_need_to_outscore_unrelated_direct_context(self) -> None:
        self.write_graph(
            "launch-plan",
            graph_node(
                "launch-plan",
                "Coordinate the zephyr launch.",
                node_type="plan",
                managed="true",
            ),
        )
        self.write_graph(
            "launch-evidence",
            graph_node(
                "launch-evidence",
                "Zephyr launch evidence review zephyr launch evidence review.",
            ),
        )

        payload = recall_bundle(self.root, "zephyr launch evidence review")
        ids = [item["id"] for item in payload["results"]]

        self.assertEqual("selected", payload["plan_context"]["state"])
        self.assertEqual("launch-plan", ids[0])
        self.assertIn("launch-evidence", ids)

    def test_incidental_word_in_a_long_plan_body_does_not_activate_it(self) -> None:
        self.write_graph(
            "operations-plan",
            graph_node(
                "operations-plan",
                "Coordinate the internal operations cadence.",
                node_type="plan",
                managed="true",
                body="# Operations Plan\n\nThe archive happens to mention cobalt once.\n",
            ),
        )
        self.write_graph(
            "cobalt-review",
            graph_node("cobalt-review", "Prepare the cobalt customer review."),
        )

        payload = recall_bundle(self.root, "cobalt customer review")

        self.assertEqual("none", payload["plan_context"]["state"])
        self.assertEqual("cobalt-review", payload["results"][0]["id"])

    def test_get_returns_full_body_hash_citations_and_legacy_lineage(self) -> None:
        body = "# Launch Plan\n\n" + "A complete free-form plan body. " * 20
        self.write_graph(
            "launch-plan",
            graph_node(
                "launch-plan",
                "Coordinate the launch.",
                node_type="plan",
                managed="true",
                body=body,
            ),
        )

        result = get_record(self.root, "launch-plan")

        self.assertEqual(body.strip(), result["body"].strip())
        self.assertEqual(64, len(result["content_hash"]))
        self.assertEqual("example://source-one", result["sources"][0]["pointer"])
        self.assertEqual("legacy", result["lineage"]["status"])

    def test_get_requires_kind_only_when_record_id_is_ambiguous(self) -> None:
        self.write_graph("home", graph_node("home", "The graph home record."))
        atomic_write(
            self.root / "indexes/home.md",
            """---
id: home
title: Home Index
graph_ids: [home]
---

# Home Index
""",
        )

        with self.assertRaisesRegex(Exception, "ambiguous"):
            get_record(self.root, "home")
        self.assertEqual("index", get_record(self.root, "home", kind="index")["kind"])

    def test_get_reads_complete_source_cards(self) -> None:
        result = get_record(self.root, "source-one", kind="source")

        self.assertEqual("source", result["kind"])
        self.assertEqual("example://source-one", result["frontmatter"]["pointer"])
        self.assertIn("# Source", result["body"])
        self.assertEqual(64, len(result["content_hash"]))


if __name__ == "__main__":
    unittest.main()
