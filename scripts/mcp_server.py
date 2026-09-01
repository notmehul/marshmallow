#!/usr/bin/env python3
"""A stdlib-only MCP server exposing Marshmallow's bounded agent loop.

The whole point is zero resistance for any model: instead of a runtime.md ritual
the agent must remember to follow, it sees self-describing tools. The tool
descriptions ARE the instructions, so a non-Claude harness gets the same "recall
before you act, capture instead of forgetting" behavior with no extra wiring.

Only bounded verbs are exposed:

- ``recall``   - navigate source-backed context plus bounded guidance (read-only).
- ``get``      - read one complete recalled record (read-only).
- ``history``  - inspect managed revisions (read-only).
- ``maintain`` - update only pre-authorized managed graph state.
- ``remember`` - capture into the untrusted inbox (never touches the graph).
- ``pending``  - list candidates awaiting human review (read-only).

Promotion is deliberately absent. Crossing a candidate into the trusted graph is
the human gate; exposing it here would let any model bypass the one guarantee
that makes Marshmallow auditable. Promote stays a deliberate act via the CLI or
``/marshmallow:learn``.

Transport is newline-delimited JSON-RPC 2.0 over stdio (the MCP stdio contract),
implemented in the standard library so Marshmallow stays dependency-free.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

from capture import list_candidates, remember
from managed_state import apply_maintenance, maintenance_history
from marshmallow_workspace import MarshmallowError, default_workspace, ensure_workspace
from personal_guidance import recall_with_personal_guidance
from record_access import get_record

PROTOCOL_VERSION = "2025-11-25"
SUPPORTED_PROTOCOL_VERSIONS = (PROTOCOL_VERSION, "2025-06-18")
SERVER_INFO = {"name": "marshmallow", "version": "0.8.0"}
DEFAULT_RECALL_LIMIT = 8
DEFAULT_PENDING_LIMIT = 20

TOOLS: list[dict[str, Any]] = [
    {
        "name": "recall",
        "description": (
            "Recall source-backed continuity for explicit prior-context requests, named people, "
            "projects or decisions, and managed-plan work. Skip generic self-contained tasks. "
            "May return one selected plan or several candidates, plus a tightly bounded "
            "personal-guidance layer showing how the work should be done. Snippets are navigation "
            "aids; call get before using a matched record."
        ),
        "inputSchema": {
            "type": "object",
            "properties": {
                "query": {"type": "string", "description": "Task, person, decision, or topic to find context for."},
                "limit": {"type": "integer", "description": "Maximum results (default 8)."},
            },
            "required": ["query"],
        },
    },
    {
        "name": "get",
        "description": (
            "Read one complete record returned by recall, including its full Markdown body, "
            "content hash, source citations, graph links, and managed-lineage status."
        ),
        "inputSchema": {
            "type": "object",
            "properties": {
                "id": {"type": "string", "description": "Record id returned by recall."},
                "kind": {
                    "type": "string",
                    "enum": ["graph", "source", "index", "projection", "recall-packet"],
                    "description": "Required only when an id is ambiguous across record kinds.",
                },
            },
            "required": ["id"],
        },
    },
    {
        "name": "history",
        "description": "Read immutable managed-update receipts for one graph node. Read-only.",
        "inputSchema": {
            "type": "object",
            "properties": {"id": {"type": "string", "description": "Managed graph node id."}},
            "required": ["id"],
        },
    },
    {
        "name": "maintain",
        "description": (
            "After completing work under a recalled managed plan, atomically update that existing "
            "plan and eligible one-hop managed nodes. Requires expected hashes and evidence, creates "
            "an immutable source receipt, and cannot create, delete, or relink graph nodes."
        ),
        "inputSchema": {
            "type": "object",
            "properties": {
                "mode": {
                    "type": "string",
                    "enum": ["update", "reconcile"],
                    "description": (
                        "Use update for semantic changes. Reconcile only records current bytes and "
                        "updates must contain id and expected_hash only."
                    ),
                },
                "plan_id": {"type": "string", "description": "Selected active managed plan id."},
                "selection_reason": {
                    "type": "string",
                    "description": "Why this plan covers the completed work.",
                },
                "outcome": {"type": "string", "description": "Short factual summary of what changed."},
                "actor": {"type": "string", "description": "Agent and session identifier."},
                "updates": {
                    "type": "array",
                    "minItems": 1,
                    "items": {
                        "type": "object",
                        "properties": {
                            "id": {"type": "string"},
                            "expected_hash": {"type": "string", "pattern": "^[0-9a-f]{64}$"},
                            "body": {
                                "type": "string",
                                "description": "Complete replacement Markdown body.",
                            },
                            "insight": {"type": "string"},
                            "status": {
                                "type": "string",
                                "pattern": "^[a-z0-9]+(?:-[a-z0-9]+)*$",
                            },
                        },
                        "required": ["id", "expected_hash"],
                        "additionalProperties": False,
                    },
                },
                "evidence": {
                    "type": "array",
                    "minItems": 1,
                    "items": {
                        "oneOf": [
                            {
                                "type": "object",
                                "properties": {
                                    "kind": {
                                        "type": "string",
                                        "enum": ["agent-execution", "artifact"],
                                    },
                                    "pointer": {"type": "string"},
                                    "summary": {"type": "string"},
                                },
                                "required": ["kind", "pointer", "summary"],
                                "additionalProperties": False,
                            },
                            {
                                "type": "object",
                                "properties": {
                                    "kind": {"type": "string", "enum": ["existing-source"]},
                                    "source_id": {"type": "string"},
                                },
                                "required": ["kind", "source_id"],
                                "additionalProperties": False,
                            },
                            {
                                "type": "object",
                                "properties": {
                                    "kind": {"type": "string", "enum": ["user-event"]},
                                    "pointer": {"type": "string", "description": "Session and turn origin."},
                                    "summary": {"type": "string"},
                                    "observation": {
                                        "type": "string",
                                        "description": "Smallest relevant observation.",
                                    },
                                },
                                "required": ["kind", "pointer", "summary", "observation"],
                                "additionalProperties": False,
                            },
                        ]
                    },
                },
            },
            "required": [
                "plan_id",
                "selection_reason",
                "outcome",
                "actor",
                "updates",
                "evidence",
            ],
            "additionalProperties": False,
        },
    },
    {
        "name": "remember",
        "description": (
            "Capture something worth keeping for later - a fact, decision, correction, or observation. "
            "Stored as an untrusted candidate in the inbox: it never becomes a fact and changes nothing "
            "until a human reviews and promotes it. Use this after unmistakable user feedback such as an "
            "explicit correction, reasoned acceptance or rejection, or durable decision; briefly tell the "
            "user what was captured. Do not capture generic praise or temporary task instructions."
        ),
        "inputSchema": {
            "type": "object",
            "properties": {
                "note": {"type": "string", "description": "The thing worth keeping."},
                "why": {"type": "string", "description": "Optional reason it matters."},
                "origin": {"type": "string", "description": "Optional provenance: a file path, URL, or session context."},
            },
            "required": ["note"],
        },
    },
    {
        "name": "pending",
        "description": "List captured notes awaiting human review and promotion. Read-only.",
        "inputSchema": {"type": "object", "properties": {}},
    },
]

TOOL_NAMES = {tool["name"] for tool in TOOLS}


def _format_recall(bundle: dict[str, Any]) -> str:
    results = bundle["results"]
    guidance = bundle["personal_guidance"]
    if not results and not guidance:
        return "No matching source-backed context found."
    lines: list[str] = []
    plan_context = bundle["plan_context"]
    if plan_context["state"] == "selected":
        lines.append(f"Plan-centered context: {plan_context['selected_id']}")
    elif plan_context["state"] == "candidates":
        ids = ", ".join(item["id"] for item in plan_context["candidates"])
        lines.append(f"Plan candidates (call get before selecting): {ids}")
    if results:
        lines.append("Relevant context:")
    for result in results:
        label = result["title"] or result["insight"] or result["task"] or result["id"]
        reason = f"/{result['match_reason']}" if result.get("bundle_id") else ""
        lines.append(f"- [{result['kind']}{reason}] id={result['id']} — {label}")
        if result.get("lineage_status") in {"broken", "drifted"}:
            lines.append(f"    WARNING: managed lineage is {result['lineage_status']}; reconcile before maintenance")
        if result["snippet"]:
            lines.append(f"    {result['snippet']}")
        for citation in result.get("sources", []):
            lines.append(f"    source: {citation['id']} ({citation['pointer'] or 'unresolved'})")
    if guidance:
        lines.append("Personal guidance (bounded):")
        for item in guidance:
            lines.append(f"- {item['guidance']} [{item['id']}]")
            if item["example"]:
                lines.append(f"    Example: {item['example']}")
    return "\n".join(lines)


def call_tool(name: str, arguments: dict[str, Any], root: Path) -> str:
    """Run a tool and return its text content. Raises MarshmallowError on bad input."""

    if not isinstance(arguments, dict):
        raise MarshmallowError("tool arguments must be an object")

    if name == "recall":
        query_value = arguments.get("query", "")
        if not isinstance(query_value, str):
            raise MarshmallowError("recall query must be a string")
        query = query_value.strip()
        if not query:
            raise MarshmallowError("recall requires a non-empty query")
        limit = arguments.get("limit", DEFAULT_RECALL_LIMIT)
        if not isinstance(limit, int) or isinstance(limit, bool):
            raise MarshmallowError("recall limit must be an integer")
        return _format_recall(recall_with_personal_guidance(root, query, limit=limit))
    if name == "get":
        record_id = arguments.get("id", "")
        kind = arguments.get("kind")
        if not isinstance(record_id, str) or not record_id.strip():
            raise MarshmallowError("get requires a non-empty id")
        if kind is not None and not isinstance(kind, str):
            raise MarshmallowError("get kind must be a string")
        return json.dumps(get_record(root, record_id.strip(), kind=kind), indent=2, sort_keys=True)
    if name == "history":
        node_id = arguments.get("id", "")
        if not isinstance(node_id, str) or not node_id.strip():
            raise MarshmallowError("history requires a non-empty id")
        return json.dumps({"id": node_id.strip(), "history": maintenance_history(root, node_id.strip())}, indent=2)
    if name == "maintain":
        return json.dumps(apply_maintenance(root, arguments, apply=True), indent=2, sort_keys=True)
    if name == "remember":
        note = arguments.get("note", "")
        why = arguments.get("why")
        origin = arguments.get("origin")
        if not isinstance(note, str):
            raise MarshmallowError("remember note must be a string")
        if why is not None and not isinstance(why, str):
            raise MarshmallowError("remember why must be a string")
        if origin is not None and not isinstance(origin, str):
            raise MarshmallowError("remember origin must be a string")
        _, candidate_id = remember(
            root,
            note,
            why=why,
            origin=origin,
        )
        return (
            f"Captured candidate {candidate_id} in the inbox. It is an untrusted note - nothing in "
            "the graph changed. A human can review it with `pending` and promote it via "
            "/marshmallow:learn."
        )
    if name == "pending":
        candidates = list_candidates(root)
        if not candidates:
            return "No inbox candidates awaiting promotion."
        visible = candidates[:DEFAULT_PENDING_LIMIT]
        lines = [f"- {item['id']} ({item['status']}): {item['summary']}" for item in visible]
        if len(candidates) > len(visible):
            lines.append(f"Showing {len(visible)} of {len(candidates)} pending candidates.")
        return "\n".join(lines)
    raise MarshmallowError(f"Unknown tool: {name}")


def _result(request_id: Any, result: dict[str, Any]) -> dict[str, Any]:
    return {"jsonrpc": "2.0", "id": request_id, "result": result}


def _error(request_id: Any, code: int, message: str) -> dict[str, Any]:
    return {"jsonrpc": "2.0", "id": request_id, "error": {"code": code, "message": message}}


def dispatch(request: dict[str, Any], root: Path) -> dict[str, Any] | None:
    """Handle one JSON-RPC request. Returns None for notifications (no reply)."""

    method = request.get("method")
    request_id = request.get("id")

    if method == "initialize":
        params = request.get("params") or {}
        client_version = params.get("protocolVersion") if isinstance(params, dict) else None
        protocol_version = (
            client_version if client_version in SUPPORTED_PROTOCOL_VERSIONS else PROTOCOL_VERSION
        )
        return _result(
            request_id,
            {"protocolVersion": protocol_version, "capabilities": {"tools": {}}, "serverInfo": SERVER_INFO},
        )
    if method == "ping":
        return _result(request_id, {})
    if method == "tools/list":
        return _result(request_id, {"tools": TOOLS})
    if method == "tools/call":
        try:
            params = request.get("params") or {}
            if not isinstance(params, dict):
                raise MarshmallowError("tools/call params must be an object")
            name = params.get("name", "")
            if not isinstance(name, str):
                raise MarshmallowError("tool name must be a string")
            arguments = params.get("arguments") or {}
            text = call_tool(name, arguments, root)
            is_error = False
        except (MarshmallowError, OSError) as error:
            text = f"ERROR: {error}"
            is_error = True
        return _result(request_id, {"content": [{"type": "text", "text": text}], "isError": is_error})

    # Notifications carry no id and expect no reply; unknown notifications are ignored.
    if request_id is None:
        return None
    return _error(request_id, -32601, f"Method not found: {method}")


def serve(root: Path, stdin: Any = None, stdout: Any = None) -> None:
    stdin = stdin or sys.stdin
    stdout = stdout or sys.stdout
    for line in stdin:
        line = line.strip()
        if not line:
            continue
        try:
            request = json.loads(line)
        except json.JSONDecodeError:
            continue  # Cannot recover a request id from unparseable input; skip.
        if not isinstance(request, dict):
            continue
        response = dispatch(request, root)
        if response is not None:
            stdout.write(json.dumps(response) + "\n")
            stdout.flush()


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Marshmallow MCP server (stdio).")
    parser.add_argument("--workspace", type=Path, default=default_workspace())
    args = parser.parse_args(argv)
    serve(ensure_workspace(args.workspace.expanduser()))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
