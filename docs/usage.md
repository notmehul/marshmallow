# Usage

Marshmallow is a local personalization engine for Claude Code. It learns only
from material the user deliberately provides or approves.

## First Run

Run:

```text
/marshmallow:start
```

The quick-start path asks for one loose taste pack:

- things you made
- things you like
- things you reject

Good inputs include local files, folders, pasted excerpts, screenshots, PDFs,
and URLs. Marshmallow stages every useful input under `~/.marshmallow/inbox/`
before it changes durable memory.

The agent then promotes only reusable, source-backed insight into:

```text
~/.marshmallow/sources/
~/.marshmallow/graph/
~/.marshmallow/projections/
```

The graph can be inspected at `~/.marshmallow/GRAPH.md`, but graph approval is
not a required setup chore.

## Persistent Adapter

Marshmallow previews one import block for `~/.claude/CLAUDE.md`:

```md
<!-- marshmallow:adapter:start -->
@/Users/you/.marshmallow/runtime.md
<!-- marshmallow:adapter:end -->
```

After approval, ordinary Claude Code sessions search compact projections under
`~/.marshmallow/projections/`. The adapter does not load raw sources, inbox
candidates, or the full graph by default.

## Skill Overlays

When a skill is judgment-sensitive, Marshmallow can draft a compact overlay from
3-7 relevant graph nodes. It changes defaults, quality bars, anti-patterns, and
decision rules while preserving the base skill's correct procedure.

Approved overlays live under:

```text
~/.marshmallow/overlays/
```

The target `SKILL.md` receives only a small pointer block.

## No Existing Skills

If no useful writable skills are found, Marshmallow still installs the
persistent adapter after approval. That is enough for ordinary Claude Code
sessions to use personal projections.

Optionally, Marshmallow can preview a starter user-level skill:

```text
~/.claude/skills/marshmallow-aligned-builder/SKILL.md
```

The starter skill points to:

```text
~/.marshmallow/overlays/marshmallow-aligned-builder.md
```

It is created only after a visible diff and explicit approval. Rollback deletes
the generated starter skill.

## Selective Learning

Use:

```text
/marshmallow:learn
```

when a correction, decision, preference, source, accepted output, or rejected
output should improve future work.

Learning stays explicit:

- ordinary sessions are not silently ingested
- inbox candidates are untrusted until promoted
- raw session logs do not become graph nodes or runtime projections
- weak or conflicting evidence can remain in the inbox until clarified
