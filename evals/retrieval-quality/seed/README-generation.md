# Seed Corpus — How It Was Generated

Candidate seed corpus for the retrieval-quality eval (design:
`docs/plans/2026-07-08-retrieval-quality-eval-design.md`, step 2). Generated
2026-07-08 by driving `cursor-agent -p` through the staged prompts in
`../generate_seed.sh`. NOT yet pinned: a human review gate (skim the bible,
spot-check ~10 labels, run doctor) comes before this dataset is treated as
ground truth and `baseline.json` is created.

## Universe

One fictional operator — Juno Castillo, Senior Terminal Operations Manager at
HarborLine Regional Ferry — over eight weeks (2026-04-20 to 2026-06-12).
`bible.md` is the source of truth for the universe: 13 people (two Elenas, two
Victors), 6 projects (P9-GATE / P9-GANG are the deliberate near-duplicate
pair), 48 planted facts (F01–F48), one planted contradiction (F13: crane
booking stated wrong as 2026-05-12 in R08, corrected to 2026-05-19 in R22),
and a 40-row artifact ledger (R01–R40).

The vocabulary is deliberately disjoint from `evals/retrieval-quality/fixture/`
(Copperbeam universe) and `examples/` (Loomline / relationship-intelligence
universes), so eval vocabulary cannot leak into example-workspace tests.

## Pipeline (stages, in order)

| Stage | Command | Output |
|-------|---------|--------|
| 1. Bible | `generate_seed.sh bible` | `bible.md` |
| 2. Raw material | `generate_seed.sh raw <a> <b>` (5 batches of 8) | `raw/*.md` (40) |
| 3a. Source cards | `generate_seed.sh sources <a> <b>` (4 batches of 10) | `sources/*.md` (40) |
| 3b. Node roster | `generate_seed.sh roster` (deterministic, no LLM) | `stage-out/roster.json` |
| 3c. Graph nodes | `generate_seed.sh nodes <a> <b>` (10 batches of 10) | `graph/*.md` (100) |
| 3d. Navigation | `generate_seed.sh navigation` | `indexes/home.md`, `projections/*` (2) |
| 4. Queries | `generate_seed.sh queries` (run in 3 parts via `EXTRA_NOTE`) | `../queries.jsonl` |
| 5. Adversarial verify | `generate_seed.sh verify` (loop until clean) | `verify-report.md` |

Every stage writes raw model output to `stage-out/` first; `generate_seed.sh
split <file>` places it. All creative prose (names, phrasings, artifacts,
node bodies, query wording) came from cursor-agent so the vocabulary
distribution is not the reviewing agent's own. The node roster (ids, types,
fact-to-node assignment, fact-to-source mapping) is derived deterministically
from the bible's own fact table and artifact ledger — a single-call LLM
"manifest" stage hung on prompt size and was replaced. Every cursor-agent
call is wrapped in `timeout $AGENT_TIMEOUT` (default 240s) with one retry;
stages that still time out get split smaller, not retried harder.

## Human-in-the-loop steps taken

- Reviewed the bible before running later stages (checked reserved-vocabulary
  disjointness, fact/anchor structure, ledger coverage).
- Split each stage-out file and deterministically repaired
  formatting/frontmatter only: four dangling `related_nodes` shorthand ids
  mapped to their roster ids (`p9-gate` → `p9-gate-retrofit`, `p9-gang` →
  `p9-gang-replacement`, `p9-gate-vs-p9-gang` → `rel-p9-gate-vs-p9-gang`).
  Creative content was never hand-written; contradictions with the bible were
  fixed by re-running the stage with `EXTRA_NOTE=...`.
- The first zero-result negative batch collided with workspace tokens (recall
  scores any single-token overlap); q41–q45 were regenerated with a corrective
  note listing the colliding tokens (`stage-out/queries-zr.jsonl`).
- Wrote the mechanical boilerplate that is not creative content: this file
  and `runtime.md`.
- Ran the adversarial verify stage; the first pass flagged 6 direct queries
  (generic aliases on q02/q03/q04, corpus-absent spaced alias variants on
  q05/q32, and one unsupported attribution on q07 — the raw artifact shows
  Juno authorizing the dive overtime that bible fact F10 attributed to Hana).
  All six were fixed in `queries.jsonl` (q07's claim reworded to the
  attribution the raw material supports); the re-verify pass result is in
  `verify-report.md`.
- At the human review gate (2026-07-09) the q07 drift was resolved on the
  graph side too: `graph/hana-suzuki.md` and `graph/decision-dive-overtime.md`
  still echoed the bible's misattribution (Hana authorizing the overtime the
  raw session log shows Juno authorizing). Both nodes were corrected to match
  the cited source — graph nodes model source-backed synthesis, so unlabeled
  errors belong in `raw/`, not `graph/`. The planted F13 contradiction in raw
  material is unaffected.

## Deviation: punctuation-variant aliases

The step-2 instruction asked every multi-word coined term's alias list to
carry both hyphenated and spaced spellings. Where the corpus genuinely uses
both spellings the labels do carry both; but for two coinages
(`single-contractor plan`, `mock-up inspection`) the raw artifacts and nodes
consistently hyphenate, and the adversarial verifier correctly flagged the
spaced variants as labels matching nothing in the material. The verifier's
standard won: corpus-absent variants were dropped rather than editing quoted
evidence to manufacture matches.

## Plan lineage note (PR #4)

The design calls for managed plans in active / inactive / drifted lineage
states. Managed-plan lineage frontmatter is a PR #4 feature that is NOT on
this branch, so the three plan-shaped nodes (`graph/plan-*.md`) carry plain
doctor-clean frontmatter (`type: plan`, `status: active|inactive|drifted`,
`skills: [planning]`) with clearly planned-state content:

- `plan-q2-terminal-readiness` — active.
- `plan-pier9-single-contractor` — inactive, superseded 2026-05-06.
- `plan-storm-surge-coverage-matrix` — drifted: manually edited after its
  source notes (3 deckhands vs the sourced 4).

After PR #4 merges, enable lineage frontmatter on these three nodes and wire
`expected_plan` expectations into queries so the plan-activation metrics stop
reporting `"unavailable"`.

## Regeneration

The pipeline is re-runnable but NOT deterministic (cursor-agent output varies
per run). Regenerating any stage invalidates everything downstream of it and
requires the verify stage plus the machine validation to be re-run:

```sh
scripts/marshmallow.py doctor --workspace evals/retrieval-quality/seed   # 0 errors, 0 warnings
python3 evals/retrieval-quality/run_eval.py \
  --workspace evals/retrieval-quality/seed \
  --queries evals/retrieval-quality/queries.jsonl --json /tmp/seed-report.json
python3 -m unittest discover -s tests
```
