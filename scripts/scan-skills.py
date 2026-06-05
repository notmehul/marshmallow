#!/usr/bin/env python3
"""Print Claude Code skill discovery results as JSON."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from skill_scanner import discover


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--home", type=Path, default=Path.home())
    parser.add_argument("--project", type=Path, default=Path.cwd())
    parser.add_argument("--additional", type=Path, action="append", default=[])
    args = parser.parse_args()
    print(json.dumps(discover(args.home.expanduser(), args.project.resolve(), args.additional), indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
