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
- `graph/`: typed source-backed records, including an active managed plan hub
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

Notice that recall returns `retention-proof-plan` first without dropping stronger
direct matches. JSON includes `plan_context`, candidate reasons, and result
roles. It does not read raw `sources/` or `inbox/` by default, and it does not
generate new context. For this task it also returns Meera's relevant update
guidance and one short example, within the reported alignment budget.

### 4. Get The Complete Plan

```bash
scripts/marshmallow.py get retention-proof-plan \
  --kind graph \
  --workspace examples/operator-recall \
  --json
```

`get` returns the complete free-form body, frontmatter, resolved citations,
relationships, SHA-256 hash, and managed-lineage status. Recall is navigation;
agents use this full read before a plan affects work.

### 5. Preview Managed Completion

After completing covered work, build a maintenance request with the hash from
`get`, the selected-plan rationale, actor/session ID, outcome, replacement plan
body, and evidence. Preview it before applying from the CLI:

```bash
scripts/marshmallow.py maintain preview \
  --request /path/to/maintenance-request.json \
  --workspace examples/operator-recall
```

An MCP client applies the same constrained request directly because
`managed: true` is standing authorization. A successful apply would create an
immutable source receipt, update `revision_source_id`, and make the revision
visible through `history retention-proof-plan`. This bundled demo remains
unchanged because the documented command is preview-only.

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
- Recall returns paths and snippets plus a separate, bounded personal-guidance
  layer; it does not synthesize or act.
- Weak guidance matches disappear, and no more than three examples may use 20%
  of the estimated response budget.
- `get` is the authority for complete content and optimistic-concurrency hashes.
- Managed changes are current-state projections backed by immutable receipts.
- Source cards point to real bundled fixtures.
- Skill overlays remain optional downstream tuning.
- The relationship demo proves source-backed state over time without exposing
  private data or pretending to be a CRM.
