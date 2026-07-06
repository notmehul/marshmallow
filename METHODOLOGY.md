# Methodology

Marshmallow borrows from memory and personalization projects without copying
their infrastructure burden. The beta product is source-backed recall: agents do
the work, Marshmallow gives them the context that makes the work correct.

## Principles

- Models are good at synthesis; deterministic code should handle filesystem
  mutation, evidence validation, concurrency checks, previews, history, and
  rollback.
- Recall must be source-backed enough to inspect and correct.
- Personal alignment belongs inside recall, not in a parallel profile system:
  include only relevant guidance and examples, within a fixed context budget.
- Runtime guidance should be concise because imported `CLAUDE.md` content is
  context, not hard enforcement.
- Learning must be explicit. Visible capture of unmistakable feedback may create
  an untrusted candidate; automatic ingestion into durable memory creates trust
  and quality problems faster than it creates useful context.

## Influences

| Influence | Borrowed | Not Borrowed |
| --- | --- | --- |
| GBrain-like systems | clear loops, tutorials, health checks, measurable improvement | databases, broad integrations, cron jobs |
| [Graphiti episodes](https://help.getzep.com/graphiti/core-concepts/adding-episodes) | immutable event-like provenance behind current graph state | temporal graph infrastructure |
| [Mem0 history](https://docs.mem0.ai/api-reference/memory/history-memory) | inspectable revision history | hosted memory service |
| [LangGraph checkpoints](https://docs.langchain.com/oss/python/langgraph/persistence) | recoverable state transitions | database-backed execution persistence |
| Supermemory-like products | onboarding clarity | automatic capture |
| Honcho-like systems | entities, observations, relationships, representations | hosted background reasoning as the default |
| Agent skills | portable `SKILL.md` overlays | closed skill formats |

## Shape

Marshmallow keeps the surface small:

```text
sources -> current graph state -> indexes/recall packets -> agent
                ^                         |
                +-- managed receipts <----+
```

The graph stores source-backed entities, decisions, relationships, preferences,
working rules, and managed plans. Plans stay in the graph so they can serve as
operational hubs rather than becoming a parallel document system. When recall
finds a relevant active plan, it returns that plan with a compact one-hop context
bundle; otherwise it keeps the flat ranked fallback. Agent-written indexes and
recall packets remain runtime aids rather than source truth. Recall adds a
second bounded layer of personal guidance when a matching preference or
explicitly aligned node can demonstrate how the work should be done.

Managed graph files are current-state projections, not an overwritten history.
Every tool-written revision has an immutable source receipt with evidence and
before/after hashes. This keeps Marshmallow's promise precise: every durable
state update has an inspectable provenance chain, without claiming that every
underlying source is independently true. The graph stays pleasant to read while
history, reconciliation, recovery, and rollback remain deterministic.

## Non-Goals

Marshmallow is not trying to be a second brain, an embedding database, an agent
orchestration platform, an automation system, or an always-on memory daemon. It
is a foundation people can use, inspect, fork, and extend.
