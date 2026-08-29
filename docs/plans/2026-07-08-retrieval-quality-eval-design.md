# Retrieval Quality Eval

## Decision

Build an automated retrieval-quality evaluation under `evals/retrieval-quality/`
that serves two jobs from one dataset format: a deterministic CI regression
guard for `recall.py`, and a scale sweep that measures where lexical recall
degrades as the graph grows. The same harness later benchmarks competing memory
systems (Honcho, GBrain, Mem0) through thin adapters, so dataset realism is a
first-class requirement, not a nicety.

Ground truth is fact-level, not node-level: each query labels the
answer-bearing facts (claim plus alias list) found in the raw material. A tool
scores by whether its retrieved context contains the facts, regardless of its
storage shape. This is what makes cross-tool comparison valid.

## Dataset

One fictional operator's working context over eight weeks, generated once by
`cursor-agent -p` through four staged prompts and then pinned:

1. **Universe bible**: personas, projects, timeline, relationships, planted
   ground-truth facts, deliberate near-duplicates (overlapping project
   vocabulary, shared first names).
2. **Raw material**: ~40 artifacts (meeting notes, chat logs, emails, session
   fragments) written from the bible with natural messiness.
3. **Workspace derivation**: source cards, ~100 graph nodes citing them,
   indexes, two projections, and managed plans in active, inactive, and drifted
   lineage states. The workspace must pass `doctor` cleanly.
4. **Queries and labels**: flipped-workflow. Walk the planted facts; write the
   natural query, one paraphrase variant, the alias list, and negatives whose
   answers were never planted.

A second adversarial `cursor-agent` pass verifies every label against the raw
material before pinning. After pinning, no LLM touches the eval.

The seed universe is fresh fiction, not a clone of `examples/`, so eval
vocabulary cannot leak into example-workspace tests.

## Scaler

`scale_workspace.py` grows 200/1k/5k-node tiers from the seed with a seeded
RNG: bible entities are cloned into renamed parallel universes with
systematically overlapping token vocabulary — near-miss distractors, the
structure a lexical scorer must survive. Planted facts and labels stay unique
to the original universe; clones are pure distractors. Every tier passes
`doctor`. Same seed produces byte-identical tiers, so scaled tiers are
regenerated on demand rather than committed.

Cross-tool claims rest only on the fully human-realistic seed tier. Scaled
tiers are Marshmallow-internal ceiling analysis.

## Amendment (2026-08-29): node-level ground truth is the guarded metric

The fact-level containment metric below turned out not to discriminate on the
pinned seed. Measured against the 100 seed nodes, the median labeled fact's
aliases appear in 14 nodes, 34 of 48 facts appear in ten or more, and a random
five-node draw scores fact recall@5 of about 0.5. Node bodies were also
generated from the same fact table as the labels, so every direct query's
answer node carries an alias verbatim in its `insight` line. Direct fact recall
of 1.0 was therefore a property of the generation pipeline, not of retrieval.

The harness now scores two views side by side. `node` (exact
`expected_node_ids` hits in the top-k) is the guarded headline and the only
basis for claims; `fact_containment` stays as a lenient diagnostic. Precision
is over the k-slot budget rather than the returned count. Two baseline rows
(seeded random, stdlib BM25 over graph nodes) ship with every report so a
number is always read against its floor and against the reference lexical
retriever. Cross-tool comparison still needs a token budget instead of `k`;
that is unbuilt.

## Metrics

Per tier and per tool, `run_eval.py` emits one `report.json`:

- **Fact recall@k, precision@k, MRR**: alias-based containment matching,
  normalized (lowercase, collapsed whitespace). Deterministic; no LLM judge.
- **Paraphrase delta**: the same metrics on paraphrase variants, reported as
  the gap against direct phrasing. The lexical-ceiling headline number and the
  primary input to any future embeddings decision.
- **Plan activation** (Marshmallow only): correct-selection rate,
  false-activation rate, candidate surfacing on ambiguity, and the lineage
  gate — drifted or inactive plans must never auto-select. Scored from
  recall's JSON output. Activates fully once plan-centered recall (PR #4)
  merges; the runner degrades gracefully when `plan_context` is absent.
- **Negative-query discipline**: fraction returning nothing versus confident
  junk, and junk score relative to true-positive scores.
- **Efficiency**: wall-clock per query and fact recall under the result
  budget, per tier.

CI runs the seed tier against pinned `baseline.json` with a two-point
tolerance and fails on regression: deterministic, sub-second, zero tokens.

## Layout

```text
evals/retrieval-quality/
  README.md            # what it measures, how to run, how to regenerate
  generate_seed.sh     # one-time: drives cursor-agent -p, staged prompts
  seed/                # pinned workspace + raw material + labels
  queries.jsonl        # query, paraphrase, type, facts+aliases, expectations
  scale_workspace.py   # deterministic seeded scaler
  run_eval.py          # runs a tier through an adapter, scores, reports
  adapters/            # ingest(raw_material) / retrieve(query) per tool
  baseline.json        # pinned seed-tier scores for CI
```

Stdlib-only Python, matching the rest of the repo.

## Build Order

1. **Harness first**: `run_eval.py`, scorer, Marshmallow adapter, and a
   hand-written 10-node fixture with known-answer queries. Scorer correctness
   gets unit tests in `tests/test_retrieval_eval.py` before generated data
   exists.
2. **Seed generation**: run the staged prompts plus adversarial verify; human
   review gate (skim bible, spot-check ~10 labels, run `doctor`); pin.
3. **Scaler** with property tests: doctor-clean tiers, unique planted facts,
   measurable distractor overlap, reproducible bytes.
4. **Baseline and CI**: sanity-review seed-tier numbers, pin `baseline.json`,
   add the job to the test workflow.
5. **Sweep and findings**: run 200/1k/5k; write the degradation analysis into
   the eval README.

Competitor adapters are phase two: the adapter interface exists from step 1,
but Honcho/GBrain/Mem0 implementations land only after Marshmallow's own
numbers are baselined.

## Non-Goals

No LLM-as-judge scoring, no embeddings, no hosted eval service, no committed
multi-megabyte scaled fixtures, no automatic regeneration of the pinned seed,
and no competitor adapters before the Marshmallow baseline exists.
