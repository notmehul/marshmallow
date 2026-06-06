# Trust And Rollback

Marshmallow changes durable files only through previewable commands. The user
must explicitly approve adapter installs, skill rewrites, and rollback applies.

## Boundaries

- No silent learning.
- No background capture.
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

The adapter writes one marker block in `~/.claude/CLAUDE.md` and imports
`~/.marshmallow/runtime.md`.

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
