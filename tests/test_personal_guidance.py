from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "scripts"
sys.path.insert(0, str(SCRIPTS))

from marshmallow_workspace import atomic_write, ensure_workspace  # noqa: E402
from personal_guidance import recall_with_personal_guidance  # noqa: E402
from recall import recall_context  # noqa: E402


def source_card(source_id: str) -> str:
    return f"""---
id: {source_id}
pointer: example://{source_id}
captured: 2026-06-01T00:00:00Z
labels: [product]
---

# Source
"""


def guidance_node(
    node_id: str,
    *,
    status: str = "active",
    alignment: str = "",
    applies_to: str = "[frontend-design]",
) -> str:
    alignment_line = f"alignment: {alignment}\n" if alignment else ""
    return f"""---
id: {node_id}
insight: Prefer calm hierarchy over decorative dashboard density.
type: preference
applies_to: {applies_to}
guidance: Use one strong visual idea and keep the hierarchy easy to scan.
guidance_examples:
  - Open with a clear focal point instead of a grid of decorative cards.
source_ids: [source-one]
related_nodes: []
labels: [visual-taste]
status: {status}
{alignment_line}---

# Calm Hierarchy

## Evidence

- `source-one` - repeated reviews reject decorative density that obscures the
  primary action and prefer one clear visual idea.

## Use In Work

- Start with one focal point and make the next action obvious.
"""


class PersonalGuidanceRecallTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name) / ".marshmallow"
        ensure_workspace(self.root)
        atomic_write(self.root / "sources/source-one.md", source_card("source-one"))

    def tearDown(self) -> None:
        self.temp.cleanup()

    def test_recall_automatically_adds_relevant_personal_guidance(self) -> None:
        atomic_write(self.root / "graph/calm-hierarchy.md", guidance_node("calm-hierarchy"))

        bundle = recall_with_personal_guidance(self.root, "frontend design hierarchy")

        self.assertTrue(bundle["results"])
        self.assertEqual(1, len(bundle["personal_guidance"]))
        item = bundle["personal_guidance"][0]
        self.assertEqual("calm-hierarchy", item["id"])
        self.assertIn("strong", item["guidance"])
        self.assertTrue(item["example"])
        self.assertNotIn("example://source-one", str(item))
        recalled = next(result for result in bundle["results"] if result["id"] == item["id"])
        self.assertEqual("example://source-one", recalled["sources"][0]["pointer"])

    def test_preference_can_opt_out_and_stale_guidance_is_excluded(self) -> None:
        atomic_write(
            self.root / "graph/disabled.md",
            guidance_node("disabled", alignment="false"),
        )
        atomic_write(
            self.root / "graph/historical.md",
            guidance_node("historical", status="historical"),
        )

        bundle = recall_with_personal_guidance(self.root, "frontend design hierarchy")

        self.assertEqual([], bundle["personal_guidance"])

    def test_guidance_is_relevant_to_routing_metadata(self) -> None:
        atomic_write(
            self.root / "graph/calm-hierarchy.md",
            guidance_node("calm-hierarchy", applies_to="[frontend-design]"),
        )

        bundle = recall_with_personal_guidance(self.root, "investor update")

        self.assertEqual([], bundle["personal_guidance"])

    def test_guidance_fields_are_part_of_context_retrieval(self) -> None:
        node = guidance_node("calm-hierarchy").replace(
            "Open with a clear focal point instead of a grid of decorative cards.",
            "Use constellation spacing to keep related choices together.",
        )
        atomic_write(self.root / "graph/calm-hierarchy.md", node)

        bundle = recall_with_personal_guidance(self.root, "constellation spacing")

        self.assertEqual("calm-hierarchy", bundle["results"][0]["id"])
        self.assertEqual("calm-hierarchy", bundle["personal_guidance"][0]["id"])

    def test_guidance_is_capped_by_count_and_response_share(self) -> None:
        for number in range(5):
            node = guidance_node(f"calm-hierarchy-{number}")
            node = node.replace(
                "Use one strong visual idea and keep the hierarchy easy to scan.",
                "Use calm hierarchy.",
            ).replace(
                "Open with a clear focal point instead of a grid of decorative cards.",
                "Use one focal point.",
            )
            atomic_write(
                self.root / f"graph/calm-hierarchy-{number}.md",
                node,
            )

        bundle = recall_with_personal_guidance(
            self.root,
            "frontend design hierarchy",
            token_budget=500,
        )
        budget = bundle["budget"]

        self.assertEqual(3, len(bundle["personal_guidance"]))
        self.assertLessEqual(budget["estimated_personal_guidance_tokens"], 100)
        self.assertLessEqual(budget["estimated_personal_guidance_share"], 0.2)
        self.assertLessEqual(
            budget["estimated_context_tokens"] + budget["estimated_personal_guidance_tokens"],
            500,
        )

    def test_raw_context_api_remains_a_list(self) -> None:
        atomic_write(self.root / "graph/calm-hierarchy.md", guidance_node("calm-hierarchy"))

        results = recall_context(self.root, "frontend design hierarchy")

        self.assertIsInstance(results, list)
        self.assertTrue(results)


if __name__ == "__main__":
    unittest.main()
