#!/usr/bin/env python3
"""Preview, install, or remove the user-level Claude Code Marshmallow adapter."""

from __future__ import annotations

import argparse
from pathlib import Path

from harness_adapter import default_claude_md, update_adapter
from marshmallow_workspace import MarshmallowError, default_workspace


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--workspace", type=Path, default=default_workspace())
    parser.add_argument("--approve", action="store_true")
    parser.add_argument("--remove", action="store_true")
    args = parser.parse_args()
    try:
        code, message = update_adapter(
            workspace_root=args.workspace.expanduser(),
            target=default_claude_md(),
            approve=args.approve,
            remove=args.remove,
        )
    except MarshmallowError as error:
        print(f"ERROR: {error}")
        return 1
    print(message)
    return code


if __name__ == "__main__":
    raise SystemExit(main())
