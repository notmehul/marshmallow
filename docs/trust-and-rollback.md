# Trust And Rollback

Marshmallow's deterministic integration commands change external files only
through previewable operations. The user must explicitly approve adapter
installs, skill rewrites, and rollback applies. Graph nodes explicitly marked
`managed: true` use a narrower standing authorization described below.

## Boundaries

- No silent learning.
- No background capture.
- Unmistakable user feedback may be captured visibly into the untrusted inbox;
  it is not durable learning and never enters runtime context before review.
- No upload, sync, or background service run by Marshmallow.
- No sending, posting, queueing, or automation actions.
- No required `workspace.json`.
- No generated `GRAPH.md`.
- No deterministic projection generator in v1; projections are agent-written
  Markdown recall packets.
- Raw session logs do not become graph nodes.
- Promotion and dismissal preview first; terminal candidates remain inert under
  `inbox/archive/` for provenance.
- Adapter and skill rewrites require explicit approval.
- Plugin-cache skills are not edited in place.

## Managed Graph State

Creating a graph node with `managed: true` is standing authorization for agents
to maintain that file when covered work changes its state. An active managed
plan may also coordinate updates to connected managed nodes. These updates are
task-triggered, not background learning, and do not require a new preview for
every completed step.

The authorization is deliberately narrow:

- Every ordinary update changes the selected active plan and may touch only its
  one-hop connected nodes that also set `managed: true`.
- Requests carry the SHA-256 hash returned by `get`; one mismatch rejects the
  complete batch before any writes.
- Agent execution can evidence plan progress. Connected living state needs an
  existing source, inspectable artifact, or minimally preserved observable user
  event.
- New nodes, graph relationship changes, and broader inference go through the
  inbox/promotion path. `maintain` cannot create graph nodes.

Successful maintenance publishes updated current-state nodes with one immutable
`managed-update` source receipt. The receipt records actor, outcome, selected
plan, rationale, evidence, targets, and before/after hashes. Nodes preserve their
foundational `source_ids` and point `revision_source_id` at the receipt. Previous
bytes and a transaction journal live under `backups/managed/`.

Caught failure restores every previous file. After interruption, `doctor`
reports the journal; recovery finalizes only when all planned hashes and the
receipt exist, otherwise it restores the full prior batch. Manual edits remain
readable but cause lineage drift. `maintain reconcile` creates a receipt for the
current bytes under the same evidence rules, accepts no content changes, and may
repair lineage after a plan becomes inactive. Rollback is compensating history:
it requires the receipt's applied hashes still to be current and creates a new
receipt that cites the original.

Current user instructions, project instructions, and safety rules outrank stored
plans. Marshmallow does not interpret free-form plan bodies or run a
deterministic plan executor.

CLI shape:

```bash
scripts/marshmallow.py get <node-id> --json
scripts/marshmallow.py maintain preview --request update.json
scripts/marshmallow.py maintain apply --request update.json
scripts/marshmallow.py history <node-id>
scripts/marshmallow.py maintain rollback <receipt-id>
scripts/marshmallow.py maintain rollback <receipt-id> --apply
scripts/marshmallow.py maintain reconcile --request reconcile.json
scripts/marshmallow.py maintain reconcile --request reconcile.json --apply
```

Preview validates the requested scope, hashes, evidence, and changed fields but
does not reserve a transaction. Apply assigns the receipt ID and UTC timestamp.

## Adapter

Claude Code and Codex plugins register MCP without editing global harness
configuration. One-command setup remains a clone-based fallback for Codex and
an experimental path for Cursor:

```bash
scripts/marshmallow.py setup --harness codex
scripts/marshmallow.py setup --harness codex --apply
scripts/marshmallow.py setup --harness cursor
scripts/marshmallow.py setup --harness cursor --apply
```

`setup` creates or verifies `~/.marshmallow/`, previews the adapter and MCP
registration, and writes only when you pass `--apply`.
Without `--apply`, it does not write the target `AGENTS.md` or harness MCP config.

MCP-only preview/apply:

```bash
scripts/marshmallow.py mcp preview --harness codex
scripts/marshmallow.py mcp apply --harness codex
scripts/marshmallow.py mcp preview --harness cursor
scripts/marshmallow.py mcp apply --harness cursor
scripts/marshmallow.py mcp remove --harness cursor --approve
```

Apply copies the stdio server to `~/.local/share/marshmallow/scripts/` and
writes a backup record under `~/.marshmallow/backups/mcp/` before changing
`~/.codex/config.toml` or `~/.cursor/mcp.json`. It records the selected
Marshmallow workspace in the MCP environment and refuses to replace an existing
server named `marshmallow` with a different configuration.

Preview:

```bash
scripts/marshmallow.py adapter preview
```

Apply:

```bash
scripts/marshmallow.py adapter apply
```

Remove preview:

```bash
scripts/marshmallow.py adapter remove
```

Remove apply:

```bash
scripts/marshmallow.py adapter remove --approve
```

By default the adapter writes one marker block in `~/.claude/CLAUDE.md` that
imports `~/.marshmallow/runtime.md`. For other harnesses, pass `--harness`:

```bash
scripts/marshmallow.py adapter apply --harness codex   # ~/.codex/AGENTS.md
scripts/marshmallow.py adapter apply --harness cursor  # ./AGENTS.md
```

`AGENTS.md` has no import directive, so Codex and Cursor get a short pointer
block that tells the agent to read `~/.marshmallow/runtime.md`. Every harness
uses the same preview, approval, backup, and rollback shape.

## Overlays

Preview:

```bash
scripts/marshmallow.py overlay preview --skill /path/to/SKILL.md --overlay /path/to/overlay.md
```

Apply:

```bash
scripts/marshmallow.py overlay apply --skill /path/to/SKILL.md --overlay /path/to/overlay.md
```

Rollback preview:

```bash
scripts/marshmallow.py overlay rollback --skill /path/to/SKILL.md
```

Rollback apply:

```bash
scripts/marshmallow.py overlay rollback --skill /path/to/SKILL.md --approve
```

Each apply writes backup bytes and a `record.json` beside them under
`~/.marshmallow/backups/`. Rollback restores the backed-up skill exactly and
restores or removes the overlay file according to that record.

## Doctor

Run:

```bash
scripts/marshmallow.py doctor
```

Doctor checks workspace shape, source-backed graph validation, managed receipt
lineage and interrupted journals, index and recall-packet references, adapter
status, skill discovery, and backup counts. It is a health check, not an
approval gate.

## Recall

Run:

```bash
scripts/marshmallow.py recall "investor update"
```

`recall` is read-only. It searches `indexes/`, `projections/`, and `graph/` for
matching context and may expose up to three qualifying plan candidates. A
selected plan comes first without suppressing stronger direct results; remaining
space is filled with one-hop context. Use `get` before relying on a result: recall
snippets navigate, while `get` returns the complete body, citations,
relationships, hash, and lineage. Neither command searches raw inbox material or
writes, synthesizes, sends, or queues anything.
