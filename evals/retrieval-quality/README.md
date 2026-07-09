# Retrieval Quality Eval

Deterministic, stdlib-only harness that measures how well a memory tool's
retrieval surfaces planted facts. Ground truth is fact-level: each query labels
the answer-bearing facts (claim plus alias list), and a tool scores by whether
its retrieved context contains the facts after normalization (lowercase,
collapsed whitespace). No LLM judge, no network, zero tokens.

## What It Measures

- **Fact recall@k, precision@k, MRR** — alias-based containment matching over
  the top-k retrieved records.
- **Paraphrase delta** — the same metrics on each query's paraphrase variant,
  reported as the paired gap against direct phrasing. The lexical-ceiling
  headline number.
- **Negative-query discipline** — fraction of negatives returning nothing
  versus confident junk, and junk score relative to true-positive scores.
- **Plan activation** (Marshmallow only) — correct-selection rate,
  false-activation rate, candidate surfacing on ambiguity, and the lineage
  gate. Reported as `"unavailable"` until plan-centered recall emits
  `plan_context`; the runner degrades gracefully.
- **Efficiency** — wall-clock per query under the result budget (`--k`).

## How To Run

From the repo root:

```sh
python3 evals/retrieval-quality/run_eval.py \
  --workspace evals/retrieval-quality/fixture \
  --queries evals/retrieval-quality/fixture/queries.jsonl \
  --json report.json
```

`--adapter` defaults to `marshmallow`; `--k` (result budget) defaults to 5.
Omit `--json` to print the report to stdout. The Marshmallow adapter calls the
same `scripts/recall.py` functions the CLI calls — there is no second recall
implementation.

The committed `fixture/` is a hand-written 10-node Copperbeam workspace that
passes `scripts/marshmallow.py doctor --workspace evals/retrieval-quality/fixture`
cleanly, with 6 known-answer queries (each with a paraphrase variant) and 2
negatives in `fixture/queries.jsonl`.

## Query Format

One JSON object per line in `queries.jsonl`:

```json
{"id": "q1-firmware-owner",
 "text": "Who owns the Trellis One firmware at Copperbeam?",
 "paraphrase": "Which engineer is responsible for Copperbeam's firmware stack?",
 "type": "direct",
 "facts": [{"claim": "Tomas Riel owns the Trellis One firmware", "aliases": ["tomas riel"]}],
 "marshmallow": {"expected_node_ids": ["tomas-riel"]}}
```

`type` is `direct` or `negative`. Direct queries need at least one fact;
negatives carry none. The optional `marshmallow` block holds tool-specific
expectations (`expected_node_ids`, `expected_plan`) used for diagnostics and
plan-activation scoring.

## Seed Dataset (pinned 2026-07-09)

`generate_seed.sh` drove `cursor-agent -p` through the design's staged
prompts to produce `seed/` — a realistic eight-week HarborLine ferry-terminal
universe (40 raw artifacts, 40 source cards, 100 doctor-clean graph nodes,
one index, two projections) — and `queries.jsonl` (40 direct queries with
paraphrase variants and fact labels, 5 zero-result negatives, 5 lexical-junk
traps). An adversarial cursor-agent pass audited every label against the raw
artifacts (`seed/verify-report.md`, verdict CLEAN after one fix loop);
`seed/README-generation.md` documents the pipeline, repairs, and deviations.

The seed passed the human review gate on 2026-07-09 (bible skim, label
spot-checks, one graph-side attribution correction recorded in
`seed/README-generation.md`) and is pinned: it is ground truth, and
regenerating any part of it requires re-running the verify pass, the review
gate, and re-pinning `baseline.json`.

```sh
python3 evals/retrieval-quality/run_eval.py \
  --workspace evals/retrieval-quality/seed \
  --queries evals/retrieval-quality/queries.jsonl --json report.json
```

## Scale Sweep

`scale_workspace.py` grows 200/1000/5000-node tiers from the seed. Tiers are
regenerated on demand and never committed (same `--rng-seed` gives a
byte-identical tree), so generate them outside the repo:

```sh
python3 evals/retrieval-quality/scale_workspace.py \
  --seed-workspace evals/retrieval-quality/seed \
  --target-nodes 1000 --rng-seed 7 --out /tmp/tier1000

python3 evals/retrieval-quality/run_eval.py \
  --workspace /tmp/tier1000 \
  --queries evals/retrieval-quality/queries.jsonl --json report.json
```

Mechanism: the seed's 100 nodes (plus raw material, source cards, index, and
projections) are copied byte-identical, then whole 100-node parallel universes
are cloned around them as near-miss distractors — structural vocabulary
(piers, gates, vendors, berths, drills) is kept while entity names are
re-coined with partial token overlap (shared first names, `P9-GATE` becomes
`P14-GATE`, `Turnstile Dynamics` becomes e.g. `Turnbuckle Dynamics`). Every
planted-fact anchor is mutated in clones (dates shift by whole weeks,
quantities and spec codes change, anchor phrases are re-worded), so clones can
attract lexical retrieval but never contain a labeled fact — queries stay
answerable exactly as labeled, only against the original universe.
`--target-nodes` must therefore be a multiple of 100 (whole universes), at
least 200. Generation fails loudly if any anchor survives in a clone or the
tier is not doctor-clean; every tier passes `validate_workspace` and
`graph_quality_warnings` with zero errors and zero warnings by construction.
Property tests live in `tests/test_scale_workspace.py`.

## CI Regression Guard

`baseline.json` pins the seed-tier aggregates. The CI workflow runs the seed
tier on every push and fails when any guarded 0-1 metric (direct, paraphrase,
paraphrase delta, negative zero-result fraction) drifts more than the
tolerance from the pin; wall-clock and raw lexical score magnitudes are not
guarded. Changing `recall.py` legitimately (better ranking) will trip the
guard by design — review the new numbers, then re-pin by regenerating
`baseline.json` in the same commit:

```sh
python3 evals/retrieval-quality/run_eval.py \
  --workspace evals/retrieval-quality/seed \
  --queries evals/retrieval-quality/queries.jsonl \
  --json /tmp/report.json \
  --baseline evals/retrieval-quality/baseline.json   # exit 1 on drift
```

## Coming In Later Steps

Per the design's build order (`docs/plans/2026-07-08-retrieval-quality-eval-design.md`):

- Sweep findings (200/1k/5k degradation analysis).
- Competitor adapters (Honcho, GBrain, Mem0) — phase two, after the
  Marshmallow baseline exists.
