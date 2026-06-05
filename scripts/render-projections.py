#!/usr/bin/env python3
"""Render compact runtime projections from canonical Marshmallow graph nodes."""

from __future__ import annotations

import argparse
from pathlib import Path

from marshmallow_workspace import default_workspace
from projection_renderer import write_projections


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--workspace", type=Path, default=default_workspace())
    args = parser.parse_args()
    for path in write_projections(args.workspace.expanduser()):
        print(path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
