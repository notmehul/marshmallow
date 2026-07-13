# Alignment-Aware Recall Design

Date: 2026-07-13

## Decision

Recall remains Marshmallow's single runtime entrypoint. It returns two distinct
layers:

1. relevant source-backed context: facts, decisions, relationships, indexes,
   and recall packets
2. bounded personal guidance: compact instructions and examples showing how
   this user wants the work done

The second layer restores personal alignment without turning every prompt into
a profile dump or creating a parallel personalization system.

## Record Shape

Graph nodes may add these optional frontmatter fields:

```yaml
alignment: true
guidance: Start with the decision, name the tradeoff, then show the evidence.
guidance_examples:
  - Explain deliberate sequencing before discussing momentum.
```

Active `preference` nodes qualify automatically. Other node types opt in with
`alignment: true`. Any node opts out with `alignment: false`. Archived,
historical, inactive, rejected, and superseded records are excluded.

`guidance` is limited to 300 characters. `guidance_examples` contains at most
three items, each limited to 300 characters. All fields remain source-backed by
the node's required `source_ids`.

## Retrieval And Budget

`scripts/personal_guidance.py` wraps the existing raw recall function rather
than replacing it. CLI and MCP use the wrapper; internal callers that depend on
the original list response can continue to call `recall_context()`.

Guidance eligibility and ranking are deterministic:

- meaningful query terms must match node routing metadata, guidance, or examples
- candidates use the existing lexical recall score
- only the three strongest candidates may be returned
- a dependency-free character estimate budgets the response at 2,000 tokens
- context receives up to 80% of that estimate
- personal guidance has a hard 400-token ceiling and must remain at or below
  20% of the combined estimated response

Each guidance item is keyed by its graph record id instead of repeating the
record path and source citation in the second layer. The record remains
resolvable by id for deeper inspection, and raw source contents are never
inlined. One short example is fitted per item so examples demonstrate alignment
without crowding out task context.

## Trust And Priority

Recalled guidance is advisory context. The user's current request, project
instructions, and safety rules always outrank it. Weak matches are omitted
rather than padded into the prompt. Users can inspect the graph record, follow
its source pointers, correct it through the existing capture/promotion loop, or
set `alignment: false`.

## Verification

Tests cover:

- automatic guidance for relevant preference records
- explicit opt-out and stale-status exclusion
- weak-match omission
- item-count, total-budget, and 20% share limits
- CLI and MCP presentation
- graph field validation and scaffold hints
- backward compatibility of the raw recall API

## Non-Goals

- semantic embeddings or a background ranking service
- loading raw sources into every recall response
- automatic inference of sensitive personal traits
- making guidance override current instructions
- tuning skills as a prerequisite for aligned recall
