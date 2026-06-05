#!/usr/bin/env python3
"""Validate a Marshmallow workspace."""

from __future__ import annotations

import argparse
from pathlib import Path

from markdown_graph import validate_workspace
from marshmallow_workspace import default_workspace


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--workspace", type=Path, default=default_workspace())
    args = parser.parse_args()
    errors = validate_workspace(args.workspace.expanduser())
    if errors:
        for error in errors:
            print(f"ERROR: {error}")
        return 1
    print("Workspace valid.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
