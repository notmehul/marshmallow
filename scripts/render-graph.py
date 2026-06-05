#!/usr/bin/env python3
"""Render GRAPH.md from canonical Marshmallow graph nodes."""

from __future__ import annotations

import argparse
from pathlib import Path

from markdown_graph import render_graph, sync_workspace_index
from marshmallow_workspace import atomic_write, default_workspace
from projection_renderer import write_projections


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--workspace", type=Path, default=default_workspace())
    args = parser.parse_args()
    workspace = args.workspace.expanduser()
    sync_workspace_index(workspace)
    atomic_write(workspace / "GRAPH.md", render_graph(workspace))
    print(workspace / "GRAPH.md")
    for path in write_projections(workspace):
        print(path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
