#!/usr/bin/env python3
"""Source-backed transactions for existing managed graph state."""

from __future__ import annotations

import fcntl
import json
import os
import re
import secrets
from contextlib import contextmanager
from pathlib import Path
from typing import Any

from markdown_graph import (
    ID_PATTERN,
    frontmatter_scalar,
    graph_nodes,
    list_field,
    parse_frontmatter,
    readable_source_cards,
    slugify,
)
from marshmallow_workspace import (
    MarshmallowError,
    atomic_write,
    iso_timestamp,
    require_workspace,
    sha256_bytes,
    sha256_file,
    timestamp,
    write_record,
)
from recall import graph_adjacency
from record_access import get_record, managed_lineage_status, receipt_target_hashes
from safety import validate_generated_guidance

EVIDENCE_KINDS = {"agent-execution", "artifact", "existing-source", "user-event"}
INSPECTABLE_EVIDENCE_KINDS = {"artifact", "existing-source", "user-event"}
SAFE_SCALAR = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._:/+@=-]*$")
REQUEST_FIELDS = {
    "mode",
    "plan_id",
    "selection_reason",
    "outcome",
    "actor",
    "updates",
    "evidence",
}
UPDATE_FIELDS = {"id", "expected_hash", "body", "insight", "status"}


def _string(value: object, name: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise MarshmallowError(f"maintain requires a non-empty {name}")
    return value.strip()


def _reject_unknown_fields(raw: dict[str, Any], allowed: set[str], context: str) -> None:
    unknown = set(raw) - allowed
    if unknown:
        raise MarshmallowError(f"{context} has unsupported fields: {', '.join(sorted(unknown))}")


def _frontmatter_value(value: object) -> str:
    text = str(value)
    return text if SAFE_SCALAR.fullmatch(text) else frontmatter_scalar(text)


def _serialize_markdown(frontmatter: dict[str, Any], body: str) -> str:
    lines = ["---"]
    for key, value in frontmatter.items():
        if key.startswith("_"):
            continue
        if isinstance(value, list):
            if not value:
                lines.append(f"{key}: []")
                continue
            lines.append(f"{key}:")
            lines.extend(f"  - {frontmatter_scalar(item)}" for item in value)
            continue
        lines.append(f"{key}: {_frontmatter_value(value)}")
    lines.extend(("---", "", body.strip(), ""))
    return "\n".join(lines)


def _receipt_id(outcome: str) -> str:
    stem = slugify(outcome)[:40].strip("-") or "state-update"
    return f"managed-update-{timestamp().lower()}-{stem}-{secrets.token_hex(3)}"


def _validate_evidence(
    evidence: object,
    sources: dict[str, dict[str, Any]],
) -> tuple[list[dict[str, str]], list[str], list[str]]:
    if not isinstance(evidence, list) or not evidence:
        raise MarshmallowError("maintain requires at least one source-backed evidence item")

    normalized: list[dict[str, str]] = []
    basis_ids: list[str] = []
    pointers: list[str] = []
    for raw in evidence:
        if not isinstance(raw, dict):
            raise MarshmallowError("maintain evidence items must be objects")
        kind = _string(raw.get("kind"), "evidence kind")
        if kind not in EVIDENCE_KINDS:
            raise MarshmallowError(f"Unknown evidence kind {kind!r}")
        allowed = {"kind", "source_id"} if kind == "existing-source" else {"kind", "pointer", "summary"}
        if kind == "user-event":
            allowed.add("observation")
        _reject_unknown_fields(raw, allowed, f"{kind} evidence")
        item = {"kind": kind}
        if kind == "existing-source":
            source_id = _string(raw.get("source_id"), "evidence source_id")
            if source_id not in sources:
                raise MarshmallowError(f"Evidence source not found: {source_id}")
            item["source_id"] = source_id
            basis_ids.append(source_id)
        else:
            pointer = _string(raw.get("pointer"), "evidence pointer")
            summary = _string(raw.get("summary"), "evidence summary")
            validate_generated_guidance(pointer, Path("evidence pointer"), max_chars=600)
            validate_generated_guidance(summary, Path("evidence summary"), max_chars=600)
            if kind == "artifact" and not (
                pointer.startswith(("http://", "https://", "git:")) or Path(pointer).expanduser().exists()
            ):
                raise MarshmallowError(f"Artifact evidence not found: {pointer}")
            item.update(pointer=pointer, summary=summary)
            pointers.append(pointer)
            if kind == "user-event":
                observation = _string(raw.get("observation"), "user-event observation")
                validate_generated_guidance(observation, Path("user-event observation"), max_chars=600)
                item["observation"] = observation
        normalized.append(item)
    return normalized, basis_ids, pointers


def _normalize_updates(request: dict[str, Any]) -> list[dict[str, Any]]:
    raw_updates = request.get("updates")
    if not isinstance(raw_updates, list) or not raw_updates:
        raise MarshmallowError("maintain requires at least one update")
    updates: list[dict[str, Any]] = []
    seen: set[str] = set()
    for raw in raw_updates:
        if not isinstance(raw, dict):
            raise MarshmallowError("maintain updates must be objects")
        _reject_unknown_fields(raw, UPDATE_FIELDS, "managed update")
        node_id = _string(raw.get("id"), "update id")
        if node_id in seen:
            raise MarshmallowError(f"Duplicate managed update target: {node_id}")
        seen.add(node_id)
        expected_hash = _string(raw.get("expected_hash"), f"expected_hash for {node_id}")
        if not re.fullmatch(r"[0-9a-f]{64}", expected_hash):
            raise MarshmallowError(f"expected_hash for {node_id} must be a SHA-256 digest")
        update: dict[str, Any] = {"id": node_id, "expected_hash": expected_hash}
        for field in ("body", "insight", "status"):
            if field in raw:
                if not isinstance(raw[field], str):
                    raise MarshmallowError(f"{field} for {node_id} must be a string")
                if field in {"insight", "status"} and not raw[field].strip():
                    raise MarshmallowError(f"{field} for {node_id} must be non-empty")
                if field == "status" and not ID_PATTERN.fullmatch(raw[field]):
                    raise MarshmallowError(f"status for {node_id} must use lowercase hyphen-case")
                if field == "insight":
                    validate_generated_guidance(raw[field], Path(node_id), max_chars=600)
                if field == "body":
                    validate_generated_guidance(raw[field], Path(node_id), max_chars=20000)
                update[field] = raw[field]
        updates.append(update)
    return updates


def _validate_targets(
    root: Path,
    plan_id: str,
    updates: list[dict[str, Any]],
    evidence: list[dict[str, str]],
    mode: str,
    *,
    allow_inactive_plan: bool,
) -> tuple[dict[str, dict[str, Any]], dict[str, list[str]]]:
    nodes = graph_nodes(root)
    plan = nodes.get(plan_id)
    if not plan or str(plan.get("type", "")) != "plan":
        raise MarshmallowError(f"Managed plan not found: {plan_id}")
    if str(plan.get("managed", "")) != "true":
        raise MarshmallowError(f"Plan must set managed: true: {plan_id}")
    if mode == "update" and not allow_inactive_plan and str(plan.get("status", "")) != "active":
        raise MarshmallowError(f"Managed plan is not active: {plan_id}")

    update_ids = {item["id"] for item in updates}
    if plan_id not in update_ids:
        raise MarshmallowError("Every managed transaction must update its selected plan")

    adjacency = graph_adjacency(nodes)
    inspectable = any(item["kind"] in INSPECTABLE_EVIDENCE_KINDS for item in evidence)
    sources = readable_source_cards(root)
    for update in updates:
        node_id = str(update["id"])
        node = nodes.get(node_id)
        if not node:
            raise MarshmallowError(f"Managed target not found: {node_id}; maintain never creates graph nodes")
        if str(node.get("managed", "")) != "true":
            raise MarshmallowError(f"Managed target must set managed: true: {node_id}")
        if node_id != plan_id and node_id not in adjacency[plan_id]:
            raise MarshmallowError(f"Managed target must be within one hop of {plan_id}: {node_id}")
        if node_id != plan_id and not inspectable:
            raise MarshmallowError("Connected living-state updates require inspectable evidence")
        if sha256_file(Path(str(node["_path"]))) != update["expected_hash"]:
            raise MarshmallowError(f"Managed target changed since it was read: {node_id}")
        lineage = managed_lineage_status(root, node_id, node, sources=sources)["status"]
        if mode != "reconcile" and lineage in {"broken", "drifted"}:
            raise MarshmallowError(f"Managed target has {lineage} lineage; reconcile it first: {node_id}")
        changes_state = any(field in update for field in ("body", "insight", "status"))
        if mode == "reconcile" and changes_state:
            raise MarshmallowError("reconcile records current bytes and does not accept content changes")
        if mode == "update" and not changes_state:
            raise MarshmallowError(f"Managed update for {node_id} does not change any supported field")
    return nodes, adjacency


def _evidence_lines(evidence: list[dict[str, str]]) -> list[str]:
    lines: list[str] = []
    for item in evidence:
        if item["kind"] == "existing-source":
            lines.append(f"- existing source `{item['source_id']}`")
            continue
        lines.append(f"- {item['kind']}: {item['summary']} ({item['pointer']})")
        if item.get("observation"):
            lines.append(f"  - observed: {item['observation']}")
    return lines


def _build_receipt(
    *,
    receipt_id: str,
    captured: str,
    plan_id: str,
    outcome: str,
    selection_reason: str,
    actor: str,
    evidence: list[dict[str, str]],
    basis_ids: list[str],
    pointers: list[str],
    before_hashes: dict[str, str],
    after_hashes: dict[str, str],
    rollback_of: str,
) -> str:
    frontmatter: dict[str, Any] = {
        "id": receipt_id,
        "pointer": f"managed-update:{receipt_id}",
        "captured": captured,
        "summary": outcome,
        "labels": ["managed-update"],
        "kind": "managed-update",
        "plan_id": plan_id,
        "target_ids": list(after_hashes),
        "basis_ids": basis_ids,
        "evidence_kinds": sorted({item["kind"] for item in evidence}),
        "evidence_pointers": pointers,
        "previous_hashes": [f"{node_id}={digest}" for node_id, digest in before_hashes.items()],
        "target_hashes": [f"{node_id}={digest}" for node_id, digest in after_hashes.items()],
        "actor": actor,
    }
    if rollback_of:
        frontmatter["rollback_of"] = rollback_of
    changed = "\n".join(
        f"- `{node_id}`: `{before_hashes[node_id]}` -> `{digest}`"
        for node_id, digest in after_hashes.items()
    )
    body = f"""# {outcome}

## Activity

Plan: `{plan_id}`

Selection: {selection_reason}

Actor: `{actor}`

## Evidence

{chr(10).join(_evidence_lines(evidence))}

## Applied Changes

{changed}
"""
    return _serialize_markdown(frontmatter, body)


def _prepare_maintenance(
    root: Path,
    request: dict[str, Any],
    *,
    allow_inactive_plan: bool = False,
    rollback_of: str = "",
) -> dict[str, Any]:
    if not isinstance(request, dict):
        raise MarshmallowError("maintain request must be an object")
    _reject_unknown_fields(request, REQUEST_FIELDS, "maintain request")
    mode = str(request.get("mode", "update"))
    if mode not in {"update", "reconcile"}:
        raise MarshmallowError("maintain mode must be update or reconcile")
    plan_id = _string(request.get("plan_id"), "plan_id")
    outcome = _string(request.get("outcome"), "outcome")
    selection_reason = _string(request.get("selection_reason"), "selection_reason")
    validate_generated_guidance(outcome, Path("outcome"), max_chars=600)
    validate_generated_guidance(selection_reason, Path("selection_reason"), max_chars=600)
    actor = _string(request.get("actor"), "actor")
    updates = _normalize_updates(request)
    sources = readable_source_cards(root)
    evidence, basis_ids, pointers = _validate_evidence(request.get("evidence"), sources)
    nodes, _ = _validate_targets(
        root,
        plan_id,
        updates,
        evidence,
        mode,
        allow_inactive_plan=allow_inactive_plan,
    )

    captured = iso_timestamp()
    receipt_id = _receipt_id(outcome)
    before_hashes: dict[str, str] = {}
    after_hashes: dict[str, str] = {}
    new_contents: dict[str, str] = {}
    for update in updates:
        node_id = str(update["id"])
        node = nodes[node_id]
        path = Path(str(node["_path"]))
        frontmatter, current_body = parse_frontmatter(path)
        before_hashes[node_id] = sha256_file(path)
        for field in ("insight", "status"):
            if field in update:
                frontmatter[field] = update[field]
        frontmatter["updated"] = captured
        frontmatter["revision_source_id"] = receipt_id
        body = str(update.get("body", current_body))
        content = _serialize_markdown(frontmatter, body)
        new_contents[node_id] = content
        after_hashes[node_id] = sha256_bytes(content.encode("utf-8"))

    receipt = _build_receipt(
        receipt_id=receipt_id,
        captured=captured,
        plan_id=plan_id,
        outcome=outcome,
        selection_reason=selection_reason,
        actor=actor,
        evidence=evidence,
        basis_ids=basis_ids,
        pointers=pointers,
        before_hashes=before_hashes,
        after_hashes=after_hashes,
        rollback_of=rollback_of,
    )
    return {
        "mode": mode,
        "plan_id": plan_id,
        "outcome": outcome,
        "actor": actor,
        "receipt_id": receipt_id,
        "receipt_content": receipt,
        "receipt_path": str(root / "sources" / f"{receipt_id}.md"),
        "before_hashes": before_hashes,
        "after_hashes": after_hashes,
        "new_contents": new_contents,
        "target_paths": {node_id: str(nodes[node_id]["_path"]) for node_id in new_contents},
    }


def _record_dir(root: Path, receipt_id: str) -> Path:
    return root / "backups" / "managed" / receipt_id


@contextmanager
def _transaction_lock(root: Path):
    lock_path = root / "backups" / "managed" / ".lock"
    lock_path.parent.mkdir(parents=True, exist_ok=True)
    with lock_path.open("a+", encoding="utf-8") as handle:
        fcntl.flock(handle.fileno(), fcntl.LOCK_EX)
        try:
            yield
        finally:
            fcntl.flock(handle.fileno(), fcntl.LOCK_UN)


def _publish_file(staged: Path, destination: Path) -> None:
    destination.parent.mkdir(parents=True, exist_ok=True)
    os.replace(staged, destination)


def apply_maintenance(
    root: Path,
    request: dict[str, Any],
    *,
    apply: bool,
    _allow_inactive_plan: bool = False,
    _rollback_of: str = "",
) -> dict[str, Any]:
    """Preview or apply one recoverable, source-backed managed transaction."""

    root = require_workspace(root)
    prepared = _prepare_maintenance(
        root,
        request,
        allow_inactive_plan=_allow_inactive_plan,
        rollback_of=_rollback_of,
    )
    preview = {
        "status": "preview",
        "plan_id": prepared["plan_id"],
        "targets": list(prepared["new_contents"]),
        "before_hashes": prepared["before_hashes"],
        "transaction_metadata": "assigned-on-apply",
    }
    if not apply:
        return preview

    public = {
        "status": "preview",
        "plan_id": prepared["plan_id"],
        "receipt_id": prepared["receipt_id"],
        "receipt_path": prepared["receipt_path"],
        "targets": list(prepared["new_contents"]),
        "before_hashes": prepared["before_hashes"],
        "after_hashes": prepared["after_hashes"],
    }

    with _transaction_lock(root):
        return _commit_maintenance(root, prepared, public)


def _commit_maintenance(
    root: Path,
    prepared: dict[str, Any],
    public: dict[str, Any],
) -> dict[str, Any]:
    for node_id, expected_hash in prepared["before_hashes"].items():
        target_path = Path(prepared["target_paths"][node_id])
        if not target_path.is_file() or sha256_file(target_path) != expected_hash:
            raise MarshmallowError(f"Managed target changed before commit: {node_id}")

    receipt_path = Path(str(prepared["receipt_path"]))
    if receipt_path.exists():
        raise MarshmallowError(f"Managed update receipt already exists: {receipt_path}")
    record_dir = _record_dir(root, str(prepared["receipt_id"]))
    stage_dir = record_dir / "stage"
    stage_dir.mkdir(parents=True, exist_ok=False)
    targets: list[dict[str, str]] = []
    for node_id, content in prepared["new_contents"].items():
        destination = Path(prepared["target_paths"][node_id])
        backup = record_dir / "before" / destination.name
        staged = stage_dir / destination.name
        atomic_write(backup, destination.read_bytes())
        atomic_write(staged, content)
        targets.append(
            {
                "id": node_id,
                "path": str(destination),
                "backup_path": str(backup),
                "staged_path": str(staged),
                "before_hash": prepared["before_hashes"][node_id],
                "after_hash": prepared["after_hashes"][node_id],
            }
        )
    staged_receipt = stage_dir / receipt_path.name
    atomic_write(staged_receipt, prepared["receipt_content"])
    record_path = record_dir / "record.json"
    record: dict[str, Any] = {
        "status": "planned",
        "timestamp": iso_timestamp(),
        "receipt_id": prepared["receipt_id"],
        "receipt_path": str(receipt_path),
        "staged_receipt_path": str(staged_receipt),
        "plan_id": prepared["plan_id"],
        "outcome": prepared["outcome"],
        "actor": prepared["actor"],
        "targets": targets,
    }
    write_record(record_path, record)

    try:
        record["status"] = "applying"
        write_record(record_path, record)
        for target in targets:
            _publish_file(Path(target["staged_path"]), Path(target["path"]))
        _publish_file(staged_receipt, receipt_path)
        record["status"] = "applied"
        record["applied_at"] = iso_timestamp()
        write_record(record_path, record)
    except OSError as error:
        for target in targets:
            atomic_write(Path(target["path"]), Path(target["backup_path"]).read_bytes())
        receipt_path.unlink(missing_ok=True)
        record["status"] = "rolled-back"
        record["error"] = str(error)
        write_record(record_path, record)
        raise MarshmallowError(f"Managed transaction failed and was restored: {error}") from error

    public["status"] = "applied"
    public["record_path"] = str(record_path)
    return public


def maintenance_history(root: Path, node_id: str) -> list[dict[str, Any]]:
    root = require_workspace(root)
    history: list[dict[str, Any]] = []
    for source_id, source in readable_source_cards(root).items():
        if str(source.get("kind", "")) != "managed-update" or node_id not in list_field(source, "target_ids"):
            continue
        history.append(
            {
                "id": source_id,
                "captured": str(source.get("captured", "")),
                "summary": str(source.get("summary", "")),
                "actor": str(source.get("actor", "")),
                "plan_id": str(source.get("plan_id", "")),
                "basis_ids": list_field(source, "basis_ids"),
                "evidence_kinds": list_field(source, "evidence_kinds"),
                "evidence_pointers": list_field(source, "evidence_pointers"),
                "previous_hash": dict(
                    item.split("=", 1) for item in list_field(source, "previous_hashes") if "=" in item
                ).get(node_id, ""),
                "target_hash": receipt_target_hashes(source).get(node_id, ""),
                "rollback_of": str(source.get("rollback_of", "")),
                "path": str(source.get("_path", "")),
            }
        )
    history.sort(key=lambda item: (item["captured"], item["id"]))
    return history


def _find_transaction(root: Path, receipt_id: str) -> tuple[Path, dict[str, Any]]:
    for record_path in sorted((root / "backups" / "managed").glob("*/record.json")):
        try:
            record = json.loads(record_path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            continue
        if record.get("receipt_id") == receipt_id:
            return record_path, record
    raise MarshmallowError(f"Managed transaction not found: {receipt_id}")


def rollback_maintenance(
    root: Path,
    receipt_id: str,
    *,
    actor: str,
    apply: bool,
) -> dict[str, Any]:
    root = require_workspace(root)
    _, record = _find_transaction(root, receipt_id)
    if record.get("status") != "applied":
        raise MarshmallowError(f"Managed transaction is not applied: {receipt_id}")
    updates: list[dict[str, str]] = []
    for target in record["targets"]:
        current = Path(target["path"])
        if not current.is_file() or sha256_file(current) != target["after_hash"]:
            raise MarshmallowError(f"Cannot rollback after a later change: {target['id']}")
        backup_frontmatter, backup_body = parse_frontmatter(Path(target["backup_path"]))
        update = {
            "id": target["id"],
            "expected_hash": target["after_hash"],
            "body": backup_body,
        }
        # status and insight are optional on non-plan nodes; sending an empty
        # value would fail _normalize_updates and break the rollback.
        for field in ("insight", "status"):
            value = str(backup_frontmatter.get(field, "")).strip()
            if value:
                update[field] = value
        updates.append(update)
    request = {
        "mode": "update",
        "plan_id": record["plan_id"],
        "selection_reason": f"Compensating rollback of managed update {receipt_id}.",
        "outcome": f"Rollback {record['outcome']}",
        "actor": actor,
        "updates": updates,
        "evidence": [{"kind": "existing-source", "source_id": receipt_id}],
    }
    return apply_maintenance(
        root,
        request,
        apply=apply,
        _allow_inactive_plan=True,
        _rollback_of=receipt_id,
    )


def incomplete_transaction_warnings(root: Path) -> list[str]:
    root = require_workspace(root)
    warnings: list[str] = []
    for record_path in sorted((root / "backups" / "managed").glob("*/record.json")):
        try:
            record = json.loads(record_path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            warnings.append(f"{record_path}: managed transaction record is not valid JSON")
            continue
        if record.get("status") in {"planned", "applying"}:
            warnings.append(f"{record_path}: managed transaction is incomplete; run maintain recover")
    return warnings


def recover_incomplete_transactions(root: Path, *, apply: bool) -> dict[str, Any]:
    root = require_workspace(root)
    if apply:
        with _transaction_lock(root):
            return _recover_incomplete_transactions(root, apply=True)
    return _recover_incomplete_transactions(root, apply=False)


def _recover_incomplete_transactions(root: Path, *, apply: bool) -> dict[str, Any]:
    incomplete: list[tuple[Path, dict[str, Any]]] = []
    for record_path in sorted((root / "backups" / "managed").glob("*/record.json")):
        try:
            record = json.loads(record_path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            continue
        if record.get("status") in {"planned", "applying"}:
            incomplete.append((record_path, record))
    if not apply:
        return {"status": "preview", "transactions": [str(path) for path, _ in incomplete]}

    recovered: list[dict[str, str]] = []
    for record_path, record in incomplete:
        receipt_path = Path(record["receipt_path"])
        fully_applied = receipt_path.is_file() and all(
            Path(target["path"]).is_file() and sha256_file(Path(target["path"])) == target["after_hash"]
            for target in record["targets"]
        )
        if fully_applied:
            record["status"] = "applied"
            action = "finalized"
        else:
            for target in record["targets"]:
                atomic_write(Path(target["path"]), Path(target["backup_path"]).read_bytes())
            receipt_path.unlink(missing_ok=True)
            record["status"] = "recovered-rollback"
            action = "restored"
        record["recovered_at"] = iso_timestamp()
        write_record(record_path, record)
        recovered.append({"record": str(record_path), "action": action})
    return {"status": "recovered", "transactions": recovered}
