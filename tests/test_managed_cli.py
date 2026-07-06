from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "scripts"
sys.path.insert(0, str(SCRIPTS))

from marshmallow_workspace import atomic_write, ensure_workspace  # noqa: E402


SOURCE = """---
id: source-one
pointer: example://source-one
captured: 2026-07-05T00:00:00Z
---

# Source
"""

PLAN = """---
id: launch-plan
insight: Coordinate the source-backed launch.
type: plan
source_ids: [source-one]
related_nodes: []
managed: true
status: active
updated: 2026-07-05
---

# Launch Plan

- [ ] Ship.
"""


class ManagedCliTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name) / ".marshmallow"
        ensure_workspace(self.root)
        atomic_write(self.root / "sources/source-one.md", SOURCE)
        atomic_write(self.root / "graph/launch-plan.md", PLAN)

    def tearDown(self) -> None:
        self.temp.cleanup()

    def run_cli(self, *args: str) -> dict:
        completed = subprocess.run(
            [sys.executable, str(SCRIPTS / "marshmallow.py"), *args, "--workspace", str(self.root)],
            check=True,
            capture_output=True,
            text=True,
        )
        return json.loads(completed.stdout)

    def test_get_maintain_history_cli_round_trip(self) -> None:
        record = self.run_cli("get", "launch-plan", "--kind", "graph", "--json")
        request = {
            "plan_id": "launch-plan",
            "selection_reason": "The task explicitly names the launch plan.",
            "outcome": "Shipped the covered launch work.",
            "actor": "codex:cli-test",
            "updates": [
                {
                    "id": "launch-plan",
                    "expected_hash": record["content_hash"],
                    "body": "# Launch Plan\n\n- [x] Ship.\n",
                }
            ],
            "evidence": [
                {
                    "kind": "agent-execution",
                    "pointer": "task-run:cli-test",
                    "summary": "The agent completed the covered work.",
                }
            ],
        }
        request_path = self.root / "request.json"
        atomic_write(request_path, json.dumps(request))

        applied = self.run_cli("maintain", "apply", "--request", str(request_path))
        history = self.run_cli("history", "launch-plan", "--json")

        self.assertEqual("applied", applied["status"])
        self.assertEqual(applied["receipt_id"], history["history"][0]["id"])
        self.assertEqual("current", self.run_cli("get", "launch-plan", "--json")["lineage"]["status"])


if __name__ == "__main__":
    unittest.main()
