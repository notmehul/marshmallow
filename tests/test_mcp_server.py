from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "scripts"
SERVER = SCRIPTS / "mcp_server.py"
sys.path.insert(0, str(SCRIPTS))

from capture import remember  # noqa: E402
from marshmallow_workspace import atomic_write, ensure_workspace  # noqa: E402
from mcp_server import PROTOCOL_VERSION, TOOL_NAMES, call_tool, dispatch  # noqa: E402


def source_card(source_id: str) -> str:
    return f"""---
id: {source_id}
pointer: example://{source_id}
captured: 2026-06-01T00:00:00Z
labels: [product]
---

# Source
"""


def graph_node(node_id: str) -> str:
    return f"""---
id: {node_id}
insight: Mani now leads day-to-day at the company.
applies_to: [relationship]
source_ids: [source-one]
related_nodes: []
skills: [relationship-brief]
labels: [team]
---

# Node
"""


def guidance_node(node_id: str) -> str:
    return f"""---
id: {node_id}
insight: Prefer direct relationship briefs over generic CRM summaries.
type: preference
applies_to: [relationship-brief]
guidance: Keep the brief short and end with one thoughtful next action.
guidance_examples:
  - Close with the decision the relationship needs now.
source_ids: [source-one]
related_nodes: []
labels: [working-rule]
status: active
---

# Relationship Brief Preference

## Evidence

- `source-one` - repeated feedback favors compact briefs with a next action.
"""


class McpDispatchTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name) / ".marshmallow"
        ensure_workspace(self.root)

    def tearDown(self) -> None:
        self.temp.cleanup()

    def request(self, method: str, params: dict | None = None, request_id: int | None = 1) -> dict:
        message: dict = {"jsonrpc": "2.0", "method": method}
        if request_id is not None:
            message["id"] = request_id
        if params is not None:
            message["params"] = params
        return dispatch(message, self.root)

    def test_initialize_echoes_protocol_and_advertises_tools(self) -> None:
        response = self.request("initialize", {"protocolVersion": PROTOCOL_VERSION})
        self.assertEqual(PROTOCOL_VERSION, response["result"]["protocolVersion"])
        self.assertIn("tools", response["result"]["capabilities"])
        self.assertEqual("marshmallow", response["result"]["serverInfo"]["name"])

    def test_initialize_keeps_compatible_previous_protocol(self) -> None:
        response = self.request("initialize", {"protocolVersion": "2025-06-18"})
        self.assertEqual("2025-06-18", response["result"]["protocolVersion"])

    def test_initialize_negotiates_back_to_server_protocol(self) -> None:
        response = self.request("initialize", {"protocolVersion": "2099-01-01"})
        self.assertEqual(PROTOCOL_VERSION, response["result"]["protocolVersion"])

    def test_initialize_tolerates_malformed_protocol_version(self) -> None:
        response = self.request("initialize", {"protocolVersion": ["not", "a", "string"]})
        self.assertEqual(PROTOCOL_VERSION, response["result"]["protocolVersion"])

    def test_tools_list_exposes_only_the_safe_verbs(self) -> None:
        response = self.request("tools/list")
        names = {tool["name"] for tool in response["result"]["tools"]}
        self.assertEqual({"recall", "remember", "pending"}, names)
        # Promotion is the human gate and must never be exposed over MCP.
        self.assertNotIn("promote", names)
        self.assertNotIn("promote", TOOL_NAMES)
        for tool in response["result"]["tools"]:
            self.assertIn("inputSchema", tool)
            self.assertTrue(tool["description"])
        remember_tool = next(tool for tool in response["result"]["tools"] if tool["name"] == "remember")
        self.assertIn("unmistakable user feedback", remember_tool["description"])
        self.assertIn("Do not capture generic praise", remember_tool["description"])

    def test_notification_initialized_gets_no_response(self) -> None:
        self.assertIsNone(self.request("notifications/initialized", request_id=None))

    def test_unknown_method_returns_jsonrpc_error(self) -> None:
        response = self.request("resources/list")
        self.assertEqual(-32601, response["error"]["code"])

    def test_tools_call_recall_returns_cited_context(self) -> None:
        atomic_write(self.root / "sources/source-one.md", source_card("source-one"))
        atomic_write(self.root / "graph/mani-lead.md", graph_node("mani-lead"))
        response = self.request("tools/call", {"name": "recall", "arguments": {"query": "Mani day-to-day"}})
        self.assertFalse(response["result"]["isError"])
        text = response["result"]["content"][0]["text"]
        self.assertIn("source: source-one (example://source-one)", text)

    def test_tools_call_recall_includes_bounded_personal_guidance(self) -> None:
        atomic_write(self.root / "sources/source-one.md", source_card("source-one"))
        atomic_write(self.root / "graph/relationship-style.md", guidance_node("relationship-style"))

        response = self.request(
            "tools/call",
            {"name": "recall", "arguments": {"query": "relationship brief next action"}},
        )

        text = response["result"]["content"][0]["text"]
        self.assertIn("Personal guidance (bounded):", text)
        self.assertIn("Keep the brief short", text)
        self.assertIn("Example:", text)
        self.assertIn("source: source-one", text)

    def test_tools_call_remember_captures_and_reports_untrusted(self) -> None:
        response = self.request(
            "tools/call",
            {"name": "remember", "arguments": {"note": "Ship the MCP server", "why": "wins the reflex"}},
        )
        self.assertFalse(response["result"]["isError"])
        text = response["result"]["content"][0]["text"]
        self.assertIn("untrusted", text)
        self.assertIn("nothing in", text.lower())
        self.assertEqual(1, len(list((self.root / "inbox").glob("candidate-*.md"))))
        # Capture is not learning: the graph stays empty.
        self.assertEqual([], list((self.root / "graph").glob("*.md")))

    def test_tools_call_pending_lists_candidates(self) -> None:
        remember(self.root, "A captured observation")
        response = self.request("tools/call", {"name": "pending", "arguments": {}})
        self.assertIn("A captured observation", response["result"]["content"][0]["text"])

    def test_tools_call_pending_bounds_large_queues(self) -> None:
        for number in range(21):
            remember(self.root, f"Observation {number}")
        response = self.request("tools/call", {"name": "pending", "arguments": {}})
        text = response["result"]["content"][0]["text"]
        self.assertEqual(20, sum(line.startswith("- ") for line in text.splitlines()))
        self.assertIn("Showing 20 of 21", text)

    def test_tools_call_recall_without_query_is_a_tool_error_not_a_crash(self) -> None:
        response = self.request("tools/call", {"name": "recall", "arguments": {}})
        self.assertTrue(response["result"]["isError"])
        self.assertIn("ERROR", response["result"]["content"][0]["text"])

    def test_tools_call_bad_argument_type_is_a_tool_error_not_a_crash(self) -> None:
        response = self.request(
            "tools/call",
            {"name": "recall", "arguments": {"query": "Mani", "limit": "many"}},
        )
        self.assertTrue(response["result"]["isError"])
        self.assertIn("integer", response["result"]["content"][0]["text"])

        follow_up = self.request("tools/list", request_id=2)
        self.assertEqual({"recall", "remember", "pending"}, {tool["name"] for tool in follow_up["result"]["tools"]})

    def test_unknown_tool_is_reported_as_iserror(self) -> None:
        response = self.request("tools/call", {"name": "promote", "arguments": {"id": "x"}})
        self.assertTrue(response["result"]["isError"])
        self.assertIn("Unknown tool", response["result"]["content"][0]["text"])

    def test_call_tool_helper_rejects_unknown_tool(self) -> None:
        with self.assertRaises(Exception):
            call_tool("delete-everything", {}, self.root)


class McpStdioRoundTripTests(unittest.TestCase):
    def test_server_answers_newline_delimited_jsonrpc_over_stdio(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / ".marshmallow"
            messages = "\n".join(
                json.dumps(message)
                for message in (
                    {"jsonrpc": "2.0", "id": 1, "method": "initialize", "params": {"protocolVersion": "2025-06-18"}},
                    {"jsonrpc": "2.0", "method": "notifications/initialized"},
                    {"jsonrpc": "2.0", "id": 2, "method": "tools/list"},
                )
            ) + "\n"
            completed = subprocess.run(
                [sys.executable, str(SERVER), "--workspace", str(root)],
                input=messages,
                text=True,
                capture_output=True,
                check=False,
            )
            self.assertEqual(0, completed.returncode, completed.stderr)
            replies = [json.loads(line) for line in completed.stdout.splitlines() if line.strip()]
            # Two requests with ids, one notification with none => exactly two replies.
            self.assertEqual([1, 2], [reply["id"] for reply in replies])
            self.assertEqual("marshmallow", replies[0]["result"]["serverInfo"]["name"])


if __name__ == "__main__":
    unittest.main()
