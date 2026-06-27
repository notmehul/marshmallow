#!/usr/bin/env python3
"""A stdlib-only MCP server exposing the safe half of the Marshmallow loop.

The whole point is zero resistance for any model: instead of a runtime.md ritual
the agent must remember to follow, it sees three self-describing tools. The tool
descriptions ARE the instructions, so a non-Claude harness gets the same "recall
before you act, capture instead of forgetting" behavior with no extra wiring.

Only the safe verbs are exposed:

- ``recall``   - read source-backed context with citations (read-only).
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
from marshmallow_workspace import MarshmallowError, default_workspace, ensure_workspace
from recall import recall_context

PROTOCOL_VERSION = "2025-11-25"
SUPPORTED_PROTOCOL_VERSIONS = (PROTOCOL_VERSION, "2025-06-18")
SERVER_INFO = {"name": "marshmallow", "version": "0.6.0"}
DEFAULT_RECALL_LIMIT = 8

TOOLS: list[dict[str, Any]] = [
    {
        "name": "recall",
        "description": (
            "Recall source-backed context about a person, project, decision, or working rule "
            "BEFORE you draft, decide, or act. Returns the most relevant facts with their source "
            "citations in a single call. Use it whenever prior context could change your answer."
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
        "name": "remember",
        "description": (
            "Capture something worth keeping for later - a fact, decision, correction, or observation. "
            "Stored as an untrusted candidate in the inbox: it never becomes a fact and changes nothing "
            "until a human reviews and promotes it. Use this instead of letting context get lost."
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


def _format_recall(results: list[dict[str, Any]]) -> str:
    if not results:
        return "No matching source-backed context found."
    lines: list[str] = []
    for result in results:
        label = result["title"] or result["insight"] or result["task"] or result["id"]
        lines.append(f"- [{result['kind']}] {label}")
        if result["snippet"]:
            lines.append(f"    {result['snippet']}")
        for citation in result.get("sources", []):
            lines.append(f"    source: {citation['id']} ({citation['pointer'] or 'unresolved'})")
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
        return _format_recall(recall_context(root, query, limit=limit))
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
        return "\n".join(f"- {item['id']} ({item['status']}): {item['summary']}" for item in candidates)
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
