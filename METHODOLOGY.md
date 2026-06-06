# Methodology

Marshmallow borrows from memory and personalization projects without copying
their infrastructure burden.

## Principles

- Models are good at synthesis; deterministic code should handle filesystem
  mutation, validation, previews, and rollback.
- Personalization must be source-backed enough to inspect and correct.
- Runtime guidance should be concise because imported `CLAUDE.md` content is
  context, not hard enforcement.
- Learning must be explicit. Automatic capture creates trust and quality
  problems faster than it creates useful context.

## Influences

| Influence | Borrowed | Not Borrowed |
| --- | --- | --- |
| GBrain-like systems | clear loops, tutorials, health checks, measurable improvement | databases, broad integrations, cron jobs |
| Graphiti-like systems | provenance discipline | temporal graph infrastructure |
| Supermemory-like products | onboarding clarity | automatic capture |
| Agent skills | portable `SKILL.md` overlays | closed skill formats |

## Shape

Marshmallow keeps the surface small:

```text
sources -> graph nodes -> runtime adapter -> overlays -> explicit updates
```

The graph stores reusable insights with source ids. The adapter tells Claude to
search and load only relevant nodes. Overlays tune skills without copying the
whole graph into them.

## Non-Goals

Marshmallow is not trying to be a second brain, an embedding database, an agent
orchestration platform, or an always-on memory daemon. It is a foundation people
can use, inspect, fork, and extend.
