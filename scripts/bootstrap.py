#!/usr/bin/env python3
"""Initialize a Marshmallow workspace and inspect candidate source pointers."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from marshmallow_workspace import URL_PATTERN, default_workspace, ensure_workspace


def source_status(pointer: str) -> dict[str, str | bool]:
    if URL_PATTERN.match(pointer):
        return {
            "pointer": pointer,
            "accepted": True,
            "kind": "url",
            "message": "URL recorded. If the host agent cannot fetch it, ask the user to paste an excerpt or export the page.",
        }
    path = Path(pointer).expanduser()
    if path.exists():
        return {
            "pointer": str(path),
            "accepted": True,
            "kind": "directory" if path.is_dir() else "file",
            "message": "Local source is readable.",
        }
    return {
        "pointer": str(path),
        "accepted": False,
        "kind": "missing",
        "message": "Could not read local source. Ask the user to confirm the path, paste an excerpt, or export the file.",
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--workspace", type=Path, default=default_workspace())
    parser.add_argument("--check-source", action="append", default=[])
    args = parser.parse_args()

    workspace = ensure_workspace(args.workspace.expanduser())
    result = {
        "workspace": str(args.workspace.expanduser()),
        "schema_version": workspace["schema_version"],
        "source_checks": [source_status(pointer) for pointer in args.check_source],
    }
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
