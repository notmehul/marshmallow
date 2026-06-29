#!/usr/bin/env python3
"""Reversible MCP registration for non-Claude harnesses."""

from __future__ import annotations

import difflib
import json
import os
import re
import shutil
from pathlib import Path
from typing import Any

from marshmallow_workspace import (
    MarshmallowError,
    atomic_write,
    default_workspace,
    require_workspace,
    sha256_bytes,
    sha256_file,
    timestamp,
    write_record,
)

MCP_SERVER_NAME = "marshmallow"
MCP_RUNTIME_FILES = (
    "mcp_server.py",
    "capture.py",
    "recall.py",
    "markdown_graph.py",
    "marshmallow_workspace.py",
    "safety.py",
)

MCP_HARNESSES = ("cursor", "codex")


def default_runtime_dir() -> Path:
    override = os.environ.get("MARSHMALLOW_MCP_RUNTIME_DIR")
    if override:
        return Path(override).expanduser()
    return Path.home() / ".local" / "share" / "marshmallow" / "scripts"


def cursor_config_path() -> Path:
    override = os.environ.get("MARSHMALLOW_CURSOR_MCP")
    if override:
        return Path(override).expanduser()
    return Path.home() / ".cursor" / "mcp.json"


def codex_config_path() -> Path:
    override = os.environ.get("MARSHMALLOW_CODEX_CONFIG")
    if override:
        return Path(override).expanduser()
    return Path.home() / ".codex" / "config.toml"


def default_scripts_source() -> Path:
    return Path(__file__).resolve().parent


def runtime_server_path(runtime_dir: Path) -> Path:
    return runtime_dir / "mcp_server.py"


def cursor_server_entry(
    runtime_dir: Path | None = None,
    workspace_root: Path | None = None,
) -> dict[str, Any]:
    runtime_dir = runtime_dir or default_runtime_dir()
    workspace_root = workspace_root or default_workspace()
    return {
        "command": str(runtime_server_path(runtime_dir).resolve()),
        "env": {"MARSHMALLOW_HOME": str(workspace_root.resolve())},
    }


def install_runtime(source_dir: Path | None = None, runtime_dir: Path | None = None) -> Path:
    source_dir = source_dir or default_scripts_source()
    runtime_dir = runtime_dir or default_runtime_dir()
    runtime_dir.mkdir(parents=True, exist_ok=True)
    for name in MCP_RUNTIME_FILES:
        target = runtime_dir / name
        shutil.copy2(source_dir / name, target)
        target.chmod(target.stat().st_mode | 0o111)
    return runtime_dir


def read_json_object(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as error:
        raise MarshmallowError(f"Invalid JSON: {path} ({error})") from error
    if not isinstance(payload, dict):
        raise MarshmallowError(f"Expected JSON object: {path}")
    return payload


def merge_cursor_config(existing: dict[str, Any], entry: dict[str, Any]) -> dict[str, Any]:
    servers = existing.get("mcpServers")
    if servers is None:
        servers = {}
    elif not isinstance(servers, dict):
        raise MarshmallowError("Invalid ~/.cursor/mcp.json: mcpServers must be an object")
    merged = dict(existing)
    merged["mcpServers"] = {**servers, MCP_SERVER_NAME: entry}
    return merged


def remove_cursor_entry(existing: dict[str, Any]) -> dict[str, Any]:
    merged = dict(existing)
    servers = merged.get("mcpServers")
    if isinstance(servers, dict):
        servers = dict(servers)
        servers.pop(MCP_SERVER_NAME, None)
        if servers:
            merged["mcpServers"] = servers
        else:
            merged.pop("mcpServers", None)
    return merged


def toml_string(value: Path | str) -> str:
    return json.dumps(str(value).replace("\\", "/"))


def codex_mcp_block(server_path: Path, workspace_root: Path | None = None) -> str:
    workspace_root = workspace_root or default_workspace()
    return (
        f"[mcp_servers.{MCP_SERVER_NAME}]\n"
        f"command = {toml_string(server_path)}\n\n"
        f"[mcp_servers.{MCP_SERVER_NAME}.env]\n"
        f"MARSHMALLOW_HOME = {toml_string(workspace_root.resolve())}\n"
    )


def has_codex_mcp_section(text: str) -> bool:
    return bool(
        re.search(
            rf"^\[mcp_servers\.{re.escape(MCP_SERVER_NAME)}(?:\.|\])",
            text,
            re.MULTILINE,
        )
    )


def remove_codex_mcp_section(text: str) -> str:
    section = re.compile(r"^\[([^]]+)\]\s*$")
    kept: list[str] = []
    removing = False
    for line in text.splitlines(keepends=True):
        match = section.match(line.rstrip("\r\n"))
        if match:
            name = match.group(1)
            removing = name == f"mcp_servers.{MCP_SERVER_NAME}" or name.startswith(
                f"mcp_servers.{MCP_SERVER_NAME}."
            )
        if not removing:
            kept.append(line)
    updated = "".join(kept)
    if not updated:
        return ""
    return updated.rstrip() + "\n"


def install_codex_mcp_section(
    text: str,
    server_path: Path,
    workspace_root: Path | None = None,
) -> str:
    cleaned = remove_codex_mcp_section(text)
    if cleaned and not cleaned.endswith("\n"):
        cleaned += "\n"
    if cleaned and not cleaned.endswith("\n\n"):
        cleaned += "\n"
    return cleaned + codex_mcp_block(server_path, workspace_root)


def unified_diff(target: Path, original: str, updated: str) -> str:
    return "".join(
        difflib.unified_diff(
            original.splitlines(keepends=True),
            updated.splitlines(keepends=True),
            fromfile=str(target),
            tofile=str(target),
        )
    )


def mcp_record_dir(root: Path) -> Path:
    base = root / "backups" / "mcp" / timestamp()
    if not base.exists():
        return base
    counter = 2
    while True:
        candidate = base.with_name(f"{base.name}-{counter}")
        if not candidate.exists():
            return candidate
        counter += 1


def mcp_status(harness: str, runtime_dir: Path | None = None) -> dict[str, str]:
    runtime_dir = runtime_dir or default_runtime_dir()
    runtime_ready = runtime_server_path(runtime_dir).is_file()
    if harness == "cursor":
        path = cursor_config_path()
        if not path.exists():
            return {
                "harness": harness,
                "status": "missing",
                "target": str(path),
                "runtime": "ready" if runtime_ready else "missing",
            }
        payload = read_json_object(path)
        servers = payload.get("mcpServers", {})
        installed = isinstance(servers, dict) and MCP_SERVER_NAME in servers
        return {
            "harness": harness,
            "status": "installed" if installed else "not-installed",
            "target": str(path),
            "runtime": "ready" if runtime_ready else "missing",
        }
    if harness == "codex":
        path = codex_config_path()
        if not path.exists():
            return {
                "harness": harness,
                "status": "missing",
                "target": str(path),
                "runtime": "ready" if runtime_ready else "missing",
            }
        installed = f"[mcp_servers.{MCP_SERVER_NAME}]" in path.read_text(encoding="utf-8")
        return {
            "harness": harness,
            "status": "installed" if installed else "not-installed",
            "target": str(path),
            "runtime": "ready" if runtime_ready else "missing",
        }
    raise MarshmallowError(f"Unknown harness: {harness!r} (choose cursor or codex)")


def update_mcp(
    workspace_root: Path,
    harness: str,
    approve: bool,
    remove: bool,
    *,
    runtime_dir: Path | None = None,
    source_dir: Path | None = None,
) -> tuple[int, str]:
    workspace_root = require_workspace(workspace_root)
    runtime_dir = runtime_dir or default_runtime_dir()
    source_dir = source_dir or default_scripts_source()

    if harness == "cursor":
        target = cursor_config_path()
        if remove and not target.exists():
            return 0, json.dumps(
                {"status": "unchanged", "action": "remove", "harness": harness, "target": str(target)},
                indent=2,
            )
        original_bytes = target.read_bytes() if target.exists() else b""
        original = original_bytes.decode("utf-8")
        original_obj = read_json_object(target) if target.exists() else {}
        if remove:
            servers = original_obj.get("mcpServers", {})
            if not isinstance(servers, dict) or MCP_SERVER_NAME not in servers:
                return 0, json.dumps(
                    {"status": "unchanged", "action": "remove", "harness": harness, "target": str(target)},
                    indent=2,
                )
            updated_obj = remove_cursor_entry(original_obj)
        else:
            entry = cursor_server_entry(runtime_dir, workspace_root)
            servers = original_obj.get("mcpServers", {})
            if isinstance(servers, dict) and MCP_SERVER_NAME in servers and servers[MCP_SERVER_NAME] != entry:
                raise MarshmallowError(
                    "Cursor already has a different MCP server named 'marshmallow'; "
                    "remove or rename it before applying this registration"
                )
            if approve:
                install_runtime(source_dir, runtime_dir)
            updated_obj = merge_cursor_config(original_obj, entry)
        updated = json.dumps(updated_obj, indent=2) + "\n"
    elif harness == "codex":
        target = codex_config_path()
        original_bytes = target.read_bytes() if target.exists() else b""
        original = original_bytes.decode("utf-8")
        if remove:
            updated = remove_codex_mcp_section(original)
        else:
            server_path = runtime_server_path(runtime_dir)
            planned = install_codex_mcp_section(original, server_path, workspace_root)
            if has_codex_mcp_section(original) and planned != original:
                raise MarshmallowError(
                    "Codex already has a different MCP server named 'marshmallow'; "
                    "remove or rename it before applying this registration"
                )
            if approve:
                install_runtime(source_dir, runtime_dir)
            updated = planned
    else:
        raise MarshmallowError(f"Unknown harness: {harness!r} (choose cursor or codex)")

    updated_bytes = updated.encode("utf-8")
    action = "remove" if remove else "install"
    if updated_bytes == original_bytes:
        return 0, json.dumps({"status": "unchanged", "action": action, "harness": harness, "target": str(target)}, indent=2)

    diff = unified_diff(target, original, updated)
    if not approve:
        return 0, diff

    record_dir = mcp_record_dir(workspace_root)
    backup: Path | None = None
    if target.exists():
        backup = record_dir / target.name
        atomic_write(backup, original_bytes)
    record = {
        "timestamp": timestamp(),
        "action": action,
        "harness": harness,
        "target": str(target.resolve()),
        "backup_path": str(backup.resolve()) if backup else None,
        "target_existed": target.exists(),
        "original_hash": sha256_bytes(original_bytes),
        "planned_hash": sha256_bytes(updated_bytes),
        "runtime_dir": str(runtime_dir.resolve()),
    }
    write_record(record_dir / "record.json", record)
    target.parent.mkdir(parents=True, exist_ok=True)
    atomic_write(target, updated)
    record["applied_hash"] = sha256_file(target)
    write_record(record_dir / "record.json", record)
    return 0, json.dumps(
        {
            "status": "applied",
            "action": action,
            "harness": harness,
            "target": str(target),
            "runtime_dir": str(runtime_dir),
            "backup": str(backup) if backup else None,
            "record": str(record_dir / "record.json"),
        },
        indent=2,
    )
