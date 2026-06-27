# Demo

These demos use bundled workspaces under `examples/`. They show the beta loop
without private files, generated graph renders, databases, MCP, or automation.
All people and companies are fictional.

## Operator Recall

The `examples/operator-recall` workspace shows decision recall for a fictional
founder/investor update.

### 1. Inspect The Recall Example

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

### 2. Run Doctor

```bash
scripts/marshmallow.py doctor --workspace examples/operator-recall
```

The workspace should report valid source cards, graph nodes, one index, and one
recall packet.

### 3. Use Recall

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
It does not read raw `sources/` or `inbox/` by default, and it does not
generate new context. The agent uses the returned files to do the work.

## Relationship Intelligence

The `examples/relationship-intelligence` workspace shows the people-first wedge:
a dummy pre-meeting relationship brief for fictional founder Naya and fictional
investor Rowan.

### 1. Inspect The Relationship Example

```bash
find examples/relationship-intelligence -maxdepth 3 -type f | sort
```

You should see:

- `fixtures/`: fictional source notes
- `sources/`: source cards pointing to those fixtures
- `graph/`: source-backed entity, relationship, decision, and workflow records
- `indexes/home.md`: compact navigation for the brief flow
- `projections/rowan-pre-meeting-brief.md`: the polished pre-meeting packet

The demo task:

```text
Prepare Naya for a June 27, 2026 investor meeting with Rowan using only dummy
source-backed relationship context.
```

### 2. Run Doctor

```bash
scripts/marshmallow.py doctor --workspace examples/relationship-intelligence
```

The workspace should report four source cards, five graph nodes, one index, and
one recall packet.

### 3. Use Recall

Plain text:

```bash
scripts/marshmallow.py recall "Rowan pre-meeting relationship brief" \
  --workspace examples/relationship-intelligence
```

JSON:

```bash
scripts/marshmallow.py recall "next thoughtful action trust state" \
  --workspace examples/relationship-intelligence \
  --json
```

Notice that recall returns the relationship node, the pre-meeting workflow, the
investor persona, and the recall packet. The packet is a runtime aid; the source
truth remains in `sources/` and `graph/`.

## What To Notice

- Graph nodes are typed as entities, decisions, and relationships.
- Recall returns paths and snippets; it does not synthesize or act.
- Source cards point to real bundled fixtures.
- Skill overlays remain optional downstream tuning.
- The relationship demo proves source-backed state over time without exposing
  private data or pretending to be a CRM.
