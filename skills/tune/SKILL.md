---
name: tune
description: Retune existing Claude skills with Marshmallow graph-backed overlays, create aligned copies or starter skills, and rollback overlays with approval. Use when the user runs /marshmallow:tune or asks to personalize, retune, align, or rollback a skill.
license: MIT
compatibility: Designed for Claude Code with Python 3.11+ available locally.
---

# Marshmallow Tune

Tune skills only when the user wants Marshmallow to change durable skill
behavior. The graph supplies source-backed defaults; the target skill keeps its
own procedure.

## Choose Targets

Run:

```bash
python3 "${CLAUDE_PLUGIN_ROOT}/scripts/marshmallow.py" scan-skills --project "$PWD"
```

Recommend skills where personal taste, product judgment, writing style, design
direction, or architectural defaults materially change the result. Avoid
deterministic checklist skills unless the user explicitly asks.

## Draft Overlay

Search graph nodes directly:

```bash
rg -n "<skill|topic|label>" ~/.marshmallow/graph
```

Use `references/overlay-template.md`. Keep the overlay short, source-backed,
and scoped to defaults, quality bars, anti-patterns, and ask-when rules. Do not
copy the full graph into a skill.

## Preview And Apply

Preview:

```bash
python3 "${CLAUDE_PLUGIN_ROOT}/scripts/marshmallow.py" overlay preview \
  --skill "<skill-path>" \
  --overlay "<overlay-path>"
```

Apply only after explicit approval:

```bash
python3 "${CLAUDE_PLUGIN_ROOT}/scripts/marshmallow.py" overlay apply \
  --skill "<skill-path>" \
  --overlay "<overlay-path>"
```

For a read-only or plugin-cache skill, do not edit the cached file. Offer a
writable aligned copy instead:

```bash
python3 "${CLAUDE_PLUGIN_ROOT}/scripts/marshmallow.py" overlay apply \
  --skill "<source-skill>" \
  --overlay "<overlay-path>" \
  --aligned-copy
```

## Starter Skill

If no existing skill is worth tuning, preview a starter skill:

```bash
python3 "${CLAUDE_PLUGIN_ROOT}/scripts/marshmallow.py" starter preview --overlay "<overlay-path>"
```

Apply only after explicit approval:

```bash
python3 "${CLAUDE_PLUGIN_ROOT}/scripts/marshmallow.py" starter apply --overlay "<overlay-path>"
```

## Rollback

Preview:

```bash
python3 "${CLAUDE_PLUGIN_ROOT}/scripts/marshmallow.py" overlay rollback --skill "<skill-path>"
```

Apply only after explicit approval:

```bash
python3 "${CLAUDE_PLUGIN_ROOT}/scripts/marshmallow.py" overlay rollback --skill "<skill-path>" --approve
```

Rollback restores bytes from the backup and restores or removes the overlay
store according to the backup record beside it.
