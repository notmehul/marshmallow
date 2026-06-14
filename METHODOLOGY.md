# Methodology

Marshmallow borrows from memory and personalization projects without copying
their infrastructure burden. The beta product is source-backed recall: agents do
the work, Marshmallow gives them the context that makes the work correct.

## Principles

- Models are good at synthesis; deterministic code should handle filesystem
  mutation, validation, previews, and rollback.
- Recall must be source-backed enough to inspect and correct.
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
| Honcho-like systems | entities, observations, relationships, representations | hosted background reasoning as the default |
| Agent skills | portable `SKILL.md` overlays | closed skill formats |

## Shape

Marshmallow keeps the surface small:

```text
sources -> typed graph nodes -> indexes/recall packets -> runtime adapter -> explicit updates
```

The graph stores source-backed entities, decisions, relationships, preferences,
and working rules. Agent-written indexes and recall packets keep runtime context
compact without becoming source truth. The adapter tells Claude to load those
compact aids first, then only relevant graph nodes. Overlays still tune skills,
but they are one downstream use of the recall layer.

## Non-Goals

Marshmallow is not trying to be a second brain, an embedding database, an agent
orchestration platform, an automation system, or an always-on memory daemon. It
is a foundation people can use, inspect, fork, and extend.
