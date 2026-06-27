# Agent Authoring A/B

This evaluation tests one question: does a less-prescriptive authoring flow let
an agent produce equally trustworthy memory with less ceremony?

It does **not** compare two retrieval algorithms. Run both variants against the
same disposable copy of `examples/relationship-intelligence`, with the same
model, harness, input, and clean starting state.

## Setup

1. Copy `examples/relationship-intelligence` to a temporary directory.
2. Give the agent the absolute path to that directory as `WORKSPACE`.
3. Give it the absolute path to `rowan-follow-up.md` as `INPUT`.
4. Start a fresh session for each variant. Do not reveal the other variant.
5. Alternate variant order and run each at least five times per harness.

## Common Task

> The user explicitly approved learning from `INPUT`. Update the Marshmallow
> workspace at `WORKSPACE` so future agents recall the current Rowan
> relationship state, the changed deadline, and the next action. Preserve
> provenance, do not leave the old state presented as current, and verify the
> workspace when finished. Work only inside `WORKSPACE`. Report files changed,
> validation results, and the recall result for `Rowan next action deadline`.

## Variant A: Scaffolded Flow

Add this instruction:

> Follow the current Marshmallow learning workflow. Use its capture, promotion,
> scaffolding, and validation commands rather than hand-writing new records
> from scratch.

## Variant B: Direct Authoring

Add this instruction:

> Inspect the existing records and author or update the Markdown directly.
> Use Marshmallow's deterministic commands for capture, promotion, recall, and
> validation where useful, but own the semantic structure yourself.

## Scorecard

Quality gates; a failed gate makes the run invalid:

- `doctor` exits successfully.
- Every changed graph node cites an existing source card.
- The new source points to `INPUT` or to its promoted inbox candidate.
- No file outside `WORKSPACE` changes.

Score each valid run from 0 to 2 on each capability:

| Capability | 0 | 1 | 2 |
| --- | --- | --- | --- |
| Knowledge update | Old June 27 commitment remains current | Conflict is visible but unresolved | July 8 brief replaces the old current commitment |
| Temporal state | Dates are missing or wrong | Dates appear without clear ordering | June 27 is historical and July 8 is current |
| Relationship state | Incorrect | Partly updated | Warm-but-conditional state and paused introductions are accurate |
| Provenance | Unsupported synthesis | Broad source reference | Changed claims trace clearly to the follow-up source |
| Recall usefulness | New state is absent | New state appears with noise | Top results make the deadline and next action immediately usable |

Also record, without folding them into the quality score:

- tool calls
- repair attempts after validation
- input and output tokens when available
- wall-clock time
- user interventions

Prefer the simpler flow only when its median quality is no worse and it reduces
ceremony on at least two efficiency measures. Agent preference alone is not a
success metric.
