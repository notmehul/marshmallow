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

## Coming In Later Steps

Per the design's build order (`docs/plans/2026-07-08-retrieval-quality-eval-design.md`):

- `generate_seed.sh` + `seed/` — the pinned realistic eight-week dataset,
  generated once through staged prompts and adversarially verified.
- `scale_workspace.py` — deterministic seeded scaler for 200/1k/5k-node
  distractor tiers.
- `baseline.json` + CI job — pinned seed-tier scores with a two-point
  regression tolerance.
- Sweep findings and competitor adapters (Honcho, GBrain, Mem0).
