# Trust And Rollback

Marshmallow is designed to be inspectable and reversible.

## Safety Rules

- Skill updates are dry-run diffs by default.
- The persistent Claude adapter is dry-run by default.
- Every approved rewrite gets a timestamped backup.
- Repeated tunes replace one marker block instead of appending duplicates.
- Read-only skills are never silently modified.
- Plugin caches are never edited.
- Inbox candidates remain outside runtime context until promoted.
- Raw session logs never become graph nodes or runtime projections.
- Harness files and tuned skills point to canonical files under
  `~/.marshmallow/`.
- Generated projections and overlays reject common prompt-injection and
  credential-exfiltration patterns.

## Diagnostics

Check the local installation without telemetry:

```bash
python3 scripts/doctor.py
```

For the example workspace:

```bash
python3 scripts/doctor.py --workspace examples/builder-graph
```

## Remove Adapter

Preview removal from `~/.claude/CLAUDE.md`:

```bash
python3 scripts/install-adapter.py --remove
```

Apply after reviewing the preview:

```bash
python3 scripts/install-adapter.py --remove --approve
```

## Roll Back A Skill

Preview rollback:

```bash
python3 scripts/rollback-overlay.py /path/to/SKILL.md
```

Apply after review:

```bash
python3 scripts/rollback-overlay.py /path/to/SKILL.md --approve
```

Generated aligned copies, including the starter skill, roll back by deletion.
Existing skills roll back by restoring the recorded backup bytes.

## Delete Local Data

After removing the adapter and rolling back tuned skills, delete:

```bash
rm -rf ~/.marshmallow
```

Marshmallow does not create an account, sync data, or run a background service.
