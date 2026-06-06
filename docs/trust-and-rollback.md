# Trust And Rollback

Marshmallow changes durable files only through previewable commands. The user
must explicitly approve adapter installs, skill rewrites, and rollback applies.

## Boundaries

- No silent learning.
- No background capture.
- No upload, sync, or background service run by Marshmallow.
- No required `workspace.json`.
- No generated `GRAPH.md` or `projections/`.
- Raw session logs do not become graph nodes.
- Adapter and skill rewrites require explicit approval.
- Plugin-cache skills are not edited in place.

## Adapter

Preview:

```bash
python3 scripts/marshmallow.py adapter preview
```

Apply:

```bash
python3 scripts/marshmallow.py adapter apply
```

Remove preview:

```bash
python3 scripts/marshmallow.py adapter remove
```

Remove apply:

```bash
python3 scripts/marshmallow.py adapter remove --approve
```

By default the adapter writes one marker block in `~/.claude/CLAUDE.md` that
imports `~/.marshmallow/runtime.md`. For other harnesses, pass `--harness`:

```bash
python3 scripts/marshmallow.py adapter apply --harness codex   # ~/.codex/AGENTS.md
python3 scripts/marshmallow.py adapter apply --harness cursor  # ./AGENTS.md
```

`AGENTS.md` has no import directive, so Codex and Cursor get a short pointer
block that tells the agent to read `~/.marshmallow/runtime.md`. Every harness
uses the same preview, approval, backup, and rollback shape.

## Overlays

Preview:

```bash
python3 scripts/marshmallow.py overlay preview --skill /path/to/SKILL.md --overlay /path/to/overlay.md
```

Apply:

```bash
python3 scripts/marshmallow.py overlay apply --skill /path/to/SKILL.md --overlay /path/to/overlay.md
```

Rollback preview:

```bash
python3 scripts/marshmallow.py overlay rollback --skill /path/to/SKILL.md
```

Rollback apply:

```bash
python3 scripts/marshmallow.py overlay rollback --skill /path/to/SKILL.md --approve
```

Each apply writes backup bytes and a `record.json` beside them under
`~/.marshmallow/backups/`. Rollback restores the backed-up skill exactly and
restores or removes the overlay file according to that record.

## Doctor

Run:

```bash
python3 scripts/marshmallow.py doctor
```

Doctor checks workspace shape, source-backed graph validation, adapter status,
skill discovery, and backup counts. It is a health check, not an approval gate.
