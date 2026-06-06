# Demo

This demo uses the bundled `examples/builder-graph` workspace. It shows the
product loop without private files or generated projections.

## 1. Inspect The Example

```bash
find examples/builder-graph -maxdepth 3 -type f | sort
```

You should see:

- `fixtures/`: bundled example source material
- `sources/`: source cards pointing to those fixtures
- `graph/`: source-backed personalization nodes
- `overlays/frontend-design.md`: a demo skill overlay

## 2. Run Doctor

```bash
scripts/marshmallow.py doctor --workspace examples/builder-graph
```

The workspace should report valid source cards and graph nodes.

## 3. Preview The Adapter

Use a temporary target so the demo does not touch your real `CLAUDE.md`:

```bash
mkdir -p /tmp/marshmallow-demo/.claude
printf '# Demo Claude file\n' > /tmp/marshmallow-demo/.claude/CLAUDE.md

scripts/marshmallow.py adapter preview \
  --workspace examples/builder-graph \
  --target /tmp/marshmallow-demo/.claude/CLAUDE.md
```

Apply only if you want to see the backup record:

```bash
scripts/marshmallow.py adapter apply \
  --workspace examples/builder-graph \
  --target /tmp/marshmallow-demo/.claude/CLAUDE.md
```

## 4. Preview A Skill Overlay

Create a temporary skill:

```bash
mkdir -p /tmp/marshmallow-demo/skills/frontend-design
cat > /tmp/marshmallow-demo/skills/frontend-design/SKILL.md <<'EOF'
---
name: frontend-design
description: Build polished user interfaces and review visual direction.
---

# Frontend Design

Preserve responsive layout and accessibility.
EOF
```

Preview:

```bash
scripts/marshmallow.py overlay preview \
  --workspace examples/builder-graph \
  --skill /tmp/marshmallow-demo/skills/frontend-design/SKILL.md \
  --overlay examples/builder-graph/overlays/frontend-design.md
```

Apply after reviewing the diff:

```bash
scripts/marshmallow.py overlay apply \
  --workspace examples/builder-graph \
  --skill /tmp/marshmallow-demo/skills/frontend-design/SKILL.md \
  --overlay examples/builder-graph/overlays/frontend-design.md
```

Rollback:

```bash
scripts/marshmallow.py overlay rollback \
  --workspace examples/builder-graph \
  --skill /tmp/marshmallow-demo/skills/frontend-design/SKILL.md

scripts/marshmallow.py overlay rollback \
  --workspace examples/builder-graph \
  --skill /tmp/marshmallow-demo/skills/frontend-design/SKILL.md \
  --approve
```

## 5. What To Notice

- Source cards point to real bundled fixtures.
- Graph nodes all have `source_ids`.
- The runtime searches graph nodes directly.
- Skill files contain one pointer block, not the whole graph.
- Rollback restores exact bytes from `backups/`.
