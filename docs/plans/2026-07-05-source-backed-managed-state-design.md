# Source-Backed Managed State

## Decision

Managed graph nodes are readable current-state projections. Every tool-written
revision is preserved as an immutable `managed-update` source receipt. Plans
remain free-form graph nodes and can serve as visual and retrieval hubs without
creating a second document system or imposing a planning method.

The portable agent protocol is:

```text
recall -> get complete records and hashes -> perform work -> maintain -> source-backed state
```

Models decide semantic changes. Deterministic code owns evidence validation,
scope checks, optimistic concurrency, backups, staging, journaling, publication,
history, reconciliation, recovery, and compensating rollback.

## Retrieval

Recall attributes index and projection matches only to the Markdown line that
links a node. Common stopwords cannot activate a plan. A plan qualifies through
its concise metadata, the strongest matching one-hop node, or the strongest
link-local runtime-aid line. Incidental body words do not activate a plan.

Recall exposes up to three candidates. It selects one candidate automatically,
but multiple candidates require full `get` reads. An agent may choose only when
their scopes clearly distinguish one; otherwise the user decides. The selected
plan is returned first, stronger direct matches are retained, and remaining
result capacity is filled with connected context.

## Full Reads

`get <id>` returns complete frontmatter and body, SHA-256 content hash, resolved
citations, relationships, and managed-lineage state. IDs are searched across
graph nodes, source cards, indexes, and projections; `kind` is required only for
an ambiguous ID. CLI and MCP call the same implementation.

## Maintenance Boundary

A maintenance transaction must update the selected active `managed: true` plan.
It may update only existing one-hop connected nodes that also set
`managed: true`. It cannot change `id`, `type`, `managed`, `source_ids`, or graph
relationships, and it cannot create or delete nodes.

Reconciliation is the narrow exception to the active-plan requirement: it may
record current bytes for an inactive managed plan, but it does not authorize a
new semantic update.

Agent execution alone can evidence operational plan progress. Connected living
state requires an inspectable existing source, artifact/file/commit/URL, or an
observable user event. User-event receipts preserve the smallest relevant
observation and its session origin. Broader inference and knowledge requiring a
new node go to the inbox.

All expected hashes are checked before any write; apply serializes managed
transactions with a workspace lock and rechecks hashes at commit time. One
mismatch rejects the batch. Tool-written `updated` values are UTC timestamps. A successful batch
creates one receipt containing the plan, rationale, actor/session, outcome,
evidence, target IDs, and before/after hashes. Nodes preserve foundational
`source_ids` and set `revision_source_id` to the receipt.

## Atomicity And Lineage

The transaction backs up every prior node, stages all new bytes, writes a
journal, and publishes the receipt and nodes as one recoverable batch. A caught
failure restores all prior bytes. `doctor` reports interrupted journals;
recovery finalizes only when all planned hashes and the receipt exist, otherwise
it restores the complete previous batch.

`doctor` also verifies that `revision_source_id` resolves to a receipt targeting
the node and that the receipt's applied hash matches current bytes. Manual edits
remain readable but are marked drifted and block automatic plan maintenance.
`maintain reconcile` creates a new receipt for the current bytes under ordinary
evidence rules.

Rollback never erases history. It requires the original receipt's applied hashes
still to be current, restores the prior content through a new managed
transaction, and links the compensating receipt with `rollback_of`.

## Runtime Guidance

Runtime guidance activates recall for explicit prior-context requests, named
people/projects/decisions, and managed-plan work—not generic self-contained
tasks. Existing personal runtime files are updated manually; this feature does
not add a runtime migration or installation-state subsystem.

## Non-Goals

This design introduces no database, daemon, embeddings dependency, background
ingestion, plan parser, imposed plan-body structure, automatic expiry, graph-node
creation, or prompt-injection hardening.
