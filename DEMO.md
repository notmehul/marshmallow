# Demo

This demo uses the bundled `examples/operator-recall` workspace. It shows the
beta loop without private files, generated graph renders, databases, MCP, or
automation.

## 1. Inspect The Recall Example

```bash
find examples/operator-recall -maxdepth 3 -type f | sort
```

You should see:

- `fixtures/`: fictional source material
- `sources/`: source cards pointing to those fixtures
- `graph/`: typed source-backed records
- `indexes/home.md`: compact navigation for agents
- `projections/investor-update-recall.md`: a task-shaped recall packet

The demo task:

```text
Prepare an investor update and explain why Loomline is not raising this month.
```

## 2. Run Doctor

```bash
scripts/marshmallow.py doctor --workspace examples/operator-recall
```

The workspace should report valid source cards, graph nodes, one index, and one
recall packet.

## 3. Use Recall

Plain text:

```bash
scripts/marshmallow.py recall "investor update not raising" \
  --workspace examples/operator-recall
```

JSON:

```bash
scripts/marshmallow.py recall "Mani retention threshold" \
  --workspace examples/operator-recall \
  --json
```

Notice that recall returns matching indexes, recall packets, and graph nodes.
It does not read raw `sources/` or `inbox/` by default, and it does not generate
new context. The agent uses the returned files to do the work.

## 4. Optional Skill Overlay Demo

The older `examples/builder-graph` workspace still shows the overlay flow.

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

- Graph nodes are typed as entities, decisions, and relationships.
- Recall returns paths and snippets; it does not synthesize or act.
- Source cards point to real bundled fixtures.
- Skill overlays remain optional downstream tuning.
- Rollback still restores exact bytes from `backups/`.
