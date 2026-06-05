#!/usr/bin/env python3
"""Queue a compact inbox candidate for deliberate Marshmallow synthesis."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from candidate_queue import KINDS, queue_candidate
from marshmallow_workspace import MarshmallowError, default_workspace


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--workspace", type=Path, default=default_workspace())
    parser.add_argument("--title", required=True)
    parser.add_argument("--kind", required=True, choices=sorted(KINDS))
    parser.add_argument("--cwd")
    parser.add_argument("--source-pointer")
    parser.add_argument("--content")
    args = parser.parse_args()
    content = args.content if args.content is not None else sys.stdin.read()
    try:
        path = queue_candidate(
            root=args.workspace.expanduser(),
            title=args.title,
            kind=args.kind,
            content=content,
            cwd=args.cwd,
            source_pointer=args.source_pointer,
        )
    except MarshmallowError as error:
        print(f"ERROR: {error}")
        return 1
    print(path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
