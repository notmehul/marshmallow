# Retrieval Quality Eval

Deterministic, stdlib-only harness that measures whether a memory tool's
retrieval returns the graph nodes that answer a query. No LLM judge, no
network, zero tokens. Every report carries two baseline rows (seeded random
and stdlib BM25) so a number is always read against its floor and against the
reference lexical retriever.

## What It Measures

Two views of ground truth, side by side:

- **Node level (guarded headline).** Each direct query labels the graph nodes
  that answer it (`expected_node_ids`). Recall@k, precision@k, and MRR count
  exact id hits among the top-k graph records. An index or recall packet in a
  top-k slot is a spent slot. This is the only view used for regression
  guarding and for any claim about retrieval quality.
- **Fact containment (diagnostic).** Each query also labels answer-bearing
  facts (claim plus alias list); a fact counts as retrieved when any alias
  appears anywhere in the returned text after normalization. On the pinned
  seed this is promiscuous: the median fact's aliases appear in 14 of 100
  nodes, 34 of 48 facts appear in ten or more, and a random five-node draw
  scores fact recall@5 of about 0.5. It is reported, never guarded, and not
  a basis for claims. See the design amendment for the history.
- **Paraphrase delta.** Both views are also scored on each query's paraphrase
  variant, reported as the paired gap against direct phrasing. On the node
  view this is the lexical-ceiling headline.
- **Negative-query discipline.** Fraction of negatives returning nothing
  versus confident junk, and junk score relative to true-positive scores.
  Five negatives use vocabulary absent from the corpus and return nothing by
  construction; the other five are lexical traps and are the real signal.
- **Plan activation** (Marshmallow only). Correct-selection rate, false
  activation, candidate surfacing, lineage gate. Reported as `"unavailable"`
  until plan-centered recall emits `plan_context`.
- **Efficiency.** Wall-clock per query under the result budget (`--k`).

Precision is over the k-slot budget, not the returned count, so returning
fewer records never raises it.

## How To Run

From the repo root:

```sh
python3 evals/retrieval-quality/run_eval.py \
  --workspace evals/retrieval-quality/fixture \
  --queries evals/retrieval-quality/fixture/queries.jsonl \
  --json report.json
```

`--adapter` is one of `marshmallow` (default), `bm25`, `bm25-raw`,
`embed-graph`, `embed-raw`, or `random`; `--k` (result budget) defaults to 5.
Omit `--json` to print the report to stdout.

- `marshmallow` calls the same `scripts/recall.py` functions the CLI calls;
  there is no second recall implementation.
- `bm25` is a stdlib Okapi BM25 over graph-node files sharing Marshmallow's
  tokenizer, so the comparison isolates the scoring function. `bm25-raw` is
  the same retriever over `raw/`, the artifacts the graph was derived from:
  what a memory tool that ingests raw material would see.
- `embed-graph` and `embed-raw` are dense retrieval (BAAI/bge-small-en-v1.5,
  paragraph chunks, best-chunk cosine) over the same two corpora. This is the
  retrieval class hosted memory tools use, run locally with no API key. It
  needs the optional `fastembed` package (`uv pip install fastembed`); the
  core harness and CI stay stdlib-only and never import it.
- `random` draws k graph nodes with a fixed seed and ignores the query.

### Cross-tool mode: `--budget-tokens`

Competing tools do not share Marshmallow's node ids, and they return records
of different lengths, so top-k node hits are not a fair cross-tool metric.
`--budget-tokens N` retrieves `--k` records, keeps whole records in rank
order while they fit an estimated N-token context (about four characters per
token), and scores what fits. Fact containment under that cut is the cross-tool
number; node metrics are still reported for adapters that return graph nodes.
Precision in this mode is over the records kept.

```sh
python3 evals/retrieval-quality/run_eval.py --adapter bm25-raw --k 20 --budget-tokens 1500 \
  --workspace evals/retrieval-quality/seed --queries evals/retrieval-quality/queries.jsonl
```

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

One caveat is structural and cannot be audited away: the node roster assigned
facts to nodes from the bible's fact table, and node bodies were then written
with those anchors in them. For all 40 direct queries an answer node carries
an alias verbatim in its `insight` line. Direct-phrasing scores on this seed
are therefore an upper bound, and the paraphrase view is the number to read.

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

`baseline.json` pins the seed-tier aggregates for the `marshmallow` adapter
(re-pinned 2026-08-29 on node-level scoring). The CI workflow runs the seed
tier on every push and fails when any guarded 0-1 metric (`node.direct`,
`node.paraphrase`, `node.paraphrase_delta`, negative zero-result fraction)
drifts more than the tolerance from the pin. Fact containment, wall-clock, and
raw lexical score magnitudes are not guarded. With 40 labeled queries one
query changing rank moves recall by 0.025, so the default 0.02 tolerance
catches single-query regressions and will also flag single-query wins;
re-pin deliberately when that happens. Changing `recall.py` legitimately (better ranking) will trip the
guard by design — review the new numbers, then re-pin by regenerating
`baseline.json` in the same commit:

```sh
python3 evals/retrieval-quality/run_eval.py \
  --workspace evals/retrieval-quality/seed \
  --queries evals/retrieval-quality/queries.jsonl \
  --json /tmp/report.json \
  --baseline evals/retrieval-quality/baseline.json   # exit 1 on drift
```

## Sweep Findings (2026-08-29, rng-seed 7, k=5, node-level scoring)

Node recall / precision / MRR on direct phrasing and on the paraphrase
variant, for Marshmallow's `recall.py`, stdlib BM25, and a seeded random
draw. The fact-containment column is the lenient diagnostic, shown only to
make its non-discrimination visible.

| nodes | adapter | direct recall / prec / MRR | paraphrase recall / prec / MRR | fact-contain. direct MRR | ms/query |
| ----- | ------- | -------------------------- | ------------------------------ | ------------------------ | -------- |
| 100 | marshmallow | 0.925 / 0.405 / 0.875 | 0.588 / 0.250 / 0.627 | 1.000 | 27 |
| 100 | bm25 | 0.958 / 0.415 / 0.875 | 0.783 / 0.335 / 0.819 | 0.975 | 0 |
| 100 | random | 0.054 / 0.020 / 0.028 | 0.067 / 0.030 / 0.069 | 0.304 | 0 |
| 200 | marshmallow | 0.885 / 0.380 / 0.871 | 0.467 / 0.190 / 0.435 | 1.000 | 49 |
| 200 | bm25 | 0.942 / 0.405 / 0.850 | 0.633 / 0.260 / 0.589 | 0.975 | 1 |
| 200 | random | 0.017 / 0.010 / 0.025 | 0.054 / 0.020 / 0.044 | 0.215 | 0 |
| 1000 | marshmallow | 0.815 / 0.340 / 0.863 | 0.146 / 0.065 / 0.201 | 1.000 | 248 |
| 1000 | bm25 | 0.950 / 0.400 / 0.851 | 0.285 / 0.125 / 0.481 | 0.975 | 2 |
| 1000 | random | 0.000 / 0.000 / 0.000 | 0.000 / 0.000 / 0.000 | 0.045 | 1 |
| 5000 | marshmallow | 0.815 / 0.340 / 0.863 | 0.138 / 0.060 / 0.197 | 1.000 | 1341 |
| 5000 | bm25 | 0.950 / 0.400 / 0.879 | 0.298 / 0.130 / 0.461 | 0.988 | 14 |
| 5000 | random | 0.000 / 0.000 / 0.000 | 0.000 / 0.000 / 0.000 | 0.000 | 0 |

What the table says:

- **The old headline was leakage.** Fact-containment direct MRR stays at 1.0
  for Marshmallow at every tier, and random scores 0.3 on it at 100 nodes.
  The node view separates the three rows the way a real metric should.
- **BM25 beats `recall.py` on paraphrase at every tier.** 0.82 vs 0.63 MRR at
  100 nodes, 0.48 vs 0.20 at 1000, with recall roughly double. On direct
  phrasing the two are within noise (n=40). Marshmallow's phrase and metadata
  bonuses do not buy anything BM25's length normalization and IDF don't, and
  they cost paraphrase robustness.
- **Paraphrase collapses early for both, harder for Marshmallow.** One clone
  universe (200 nodes) costs Marshmallow 19 MRR points and BM25 23; by 1000
  nodes Marshmallow is near the floor (0.20) while BM25 holds 0.48. This is
  the lexical ceiling and it is not a 10k-node problem.
- **Direct recall is stable but precision is not.** Marshmallow returns the
  answer node in the top five 82 to 93 percent of the time across the sweep,
  yet precision sits around 0.35 to 0.40 because index and recall-packet pages
  and near-miss clones take the other slots.
- **Latency.** `recall.py` scans every file per query: 27 ms at 100 nodes,
  1.34 s at 5000. BM25 with a one-time index is 14 ms at 5000.
- **Negatives are the same across tiers by construction.** Clone vocabulary
  never touches negative-query tokens. The seed-tier number is the honest
  one: the five lexical traps all return five junk results, at 72 percent of
  true-positive score for Marshmallow and 87 percent for BM25.

Implication: at the sizes Marshmallow is designed for (tens to low hundreds
of curated nodes, agents echoing the graph's vocabulary), retrieval holds. For
the realistic case, where an agent phrases a query differently from the
stored insight, the custom scorer is the weakest of the three non-random
options at every size. The next change to `recall.py` should be measured
against the BM25 row before it lands, and any "ever-expanding graph"
direction needs vocabulary bridging or semantic retrieval first.

Caveats for anyone citing these numbers: 40 labeled queries, no confidence
intervals, one query changing rank moves recall by 0.025; distractors are
systematic clone mutations, not independently authored content; paraphrases
come from one LLM's phrasing distribution; node bodies were generated with
their answer anchors in them (see Seed Dataset), so direct-phrasing scores are
an upper bound; latency is one machine (Apple silicon, local SSD). Cross-tool
claims beyond this repo need a token budget in place of `k`, which is unbuilt.

Reproduce: generate tiers with `--rng-seed 7` as shown above and run each
adapter; identical bytes, identical scores.

## Cross-Tool Results (2026-08-29, seed tier)

Top-5 node view first, which isolates the retriever on the corpus Marshmallow
stores:

| adapter | corpus | direct node recall / MRR | paraphrase node recall / MRR | ms/query |
| --- | --- | --- | --- | --- |
| marshmallow | graph nodes | 0.925 / 0.875 | 0.588 / 0.627 | 25 |
| bm25 | graph nodes | 0.958 / 0.875 | 0.783 / 0.819 | 0 |
| embed-graph | graph nodes | 0.992 / 0.958 | 0.773 / 0.607 | 23 |
| random | graph nodes | 0.054 / 0.028 | 0.067 / 0.069 | 0 |

Then the cross-tool cut, 1500 estimated tokens of context, `--k 20`:

| adapter | corpus | direct fact recall | paraphrase fact recall | direct node recall | paraphrase node recall | records kept |
| --- | --- | --- | --- | --- | --- | --- |
| marshmallow | graph nodes | 0.988 | 0.850 | 0.700 | 0.425 | 2.0 |
| bm25 | graph nodes | 0.988 | 0.938 | 0.717 | 0.583 | 2.0 |
| embed-graph | graph nodes | 0.988 | 0.912 | 0.746 | 0.412 | 2.0 |
| bm25-raw | raw artifacts | 0.975 | 0.925 | n/a | n/a | 4.0 |
| embed-raw | raw artifacts | 0.975 | 0.850 | n/a | n/a | 4.1 |
| random | graph nodes | 0.287 | 0.375 | 0.000 | 0.033 | 2.0 |

At 1000 nodes (top-5, node view; raw-corpus rows report fact containment since they return no graph nodes):

| adapter | corpus | direct node recall / MRR | paraphrase node recall / MRR | direct fact recall | paraphrase fact recall | ms/query |
| --- | --- | --- | --- | --- | --- | --- |
| marshmallow | graph nodes | 0.815 / 0.863 | 0.146 / 0.201 | 0.988 | 0.412 | 248 |
| bm25 | graph nodes | 0.950 / 0.851 | 0.285 / 0.481 | 1.000 | 0.613 | 2 |
| embed-graph | graph nodes | 0.890 / 0.955 | 0.329 / 0.321 | 1.000 | 0.700 | 114 |
| bm25-raw | raw artifacts | n/a | n/a | 0.988 | 0.375 | 1 |
| embed-raw | raw artifacts | n/a | n/a | 0.812 | 0.475 | 47 |
| random | graph nodes | 0.000 / 0.000 | 0.000 / 0.000 | 0.087 | 0.075 | 1 |

Dense retrieval at 1000 nodes keeps the best direct MRR (0.96) and the worst
paraphrase MRR of the non-random rows (0.32, versus BM25 at 0.48).

What this says:

- **Dense embeddings do not rescue paraphrase here.** `embed-graph` has the
  best direct MRR (0.96) but its paraphrase MRR (0.61) is below BM25 (0.82)
  and level with `recall.py`. A small local model on a corpus whose
  paraphrases were written to avoid token overlap is not enough; whether a
  large hosted embedder does better is the open question the competitor rows
  would answer.
- **Raw artifacts answer as well as curated nodes on this dataset.** BM25 over
  the 40 raw files reaches the same fact recall as BM25 over the 100 graph
  nodes. That is a property of this seed (facts were planted in raw material
  and copied into nodes), and it means the eval cannot yet show the value of
  curation. A dataset that rewards synthesis (facts spread across artifacts,
  contradictions resolved in nodes) would.
- **Graph nodes are expensive context.** Seed nodes estimate at about 600
  tokens each versus about 320 for a raw artifact, so 1500 tokens holds two
  nodes or four artifacts. Node recall drops from 0.93 at top-5 to 0.70 under
  the budget for the same retriever. Recall returns pointers, but the agent
  pays that cost the moment it reads the file.
- **The random floor under budget is 0.29 to 0.38 fact recall.** Any
  cross-tool claim has to clear that, and with 40 queries the gap between the
  non-random rows (0.85 to 0.94 on paraphrase) is a handful of queries.

### Running hosted tools

The adapter contract (`ingest(dir)` then `retrieve(query, k)`) is all a tool
needs. None are wired yet because every candidate needs an LLM and an
embedding key to ingest, and a clean run needs the same key for all of them:

| tool | what it needs |
| --- | --- |
| Mem0 (OSS) | `pip install mem0ai`, an LLM key for extraction and an embedder key (or Ollama); local Qdrant is bundled |
| MemMachine | Docker (API server, Postgres+pgvector, Neo4j) and an OpenAI key; defaults to gpt-5-nano and text-embedding-3-small |
| GBrain | Bun, PGLite (no server), and a Voyage, OpenAI, or Anthropic key for embeddings |

Each would ingest `seed/raw/` and be scored with `--budget-tokens`. Expect
ingestion to cost tokens and minutes per tier; the scaled tiers are for
Marshmallow-internal analysis only.

## Coming In Later Steps

Per the design's build order (`docs/plans/2026-07-08-retrieval-quality-eval-design.md`):

- Competitor adapters (Mem0, MemMachine, GBrain) once an API key is
  available; the budget mode they need exists.
- More labeled queries (200+) with bootstrap intervals, and query types a
  memory system should be judged on: temporal ("as of week 3"), updates and
  contradictions, multi-hop across nodes.
- Plan-activation and lineage-gate metrics activate when plan-centered
  recall (PR #4) merges; re-pin `baseline.json` then.
