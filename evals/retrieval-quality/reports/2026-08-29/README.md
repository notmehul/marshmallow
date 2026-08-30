# Run reports, 2026-08-29

Raw `run_eval.py` output for every number quoted in `evals/retrieval-quality/README.md`
and in the project README. One file per (tier, mode, adapter); each holds the
aggregate and the per-query rows (retrieved ids, per-query recall, precision,
MRR, facts found and missed, wall-clock), so any table cell can be traced to
the queries behind it.

## Environment

- Apple M2, macOS 26.6.1, Python 3.12.12 (CI runs 3.11)
- Marshmallow at commit `ebb7790` on `agents/eval-cross-tool`
- fastembed 0.8.0 with `BAAI/bge-small-en-v1.5` (local, CPU)
- Gemini developer API: `gemini-embedding-001` at 768 dims (Matryoshka
  truncation), `gemini-2.5-flash` for Mem0 extraction and GBrain query expansion
- mem0ai 2.0.19, qdrant-client 1.19.0 (local on-disk Qdrant)
- gbrain 0.47.6.0, PGLite engine, `google:gemini-embedding-001` at 768 dims,
  reranker disabled (no Voyage key)

## File naming

`<tier>-<mode>-<adapter>.json`

- tier: `seed` (pinned 100-node workspace) or `tier200|1000|5000`
  (generated with `scale_workspace.py --rng-seed 7`)
- mode: `k5` (top-5, node view is the headline) or `budget1500`
  (`--k 20 --budget-tokens 1500`, fact containment is the headline)
- adapter: see the adapter list in the eval README

## Commands

```sh
# k mode
python3 evals/retrieval-quality/run_eval.py --adapter <name> \
  --workspace evals/retrieval-quality/seed --queries evals/retrieval-quality/queries.jsonl --json out.json

# budget mode
python3 evals/retrieval-quality/run_eval.py --adapter <name> --k 20 --budget-tokens 1500 \
  --workspace evals/retrieval-quality/seed --queries evals/retrieval-quality/queries.jsonl --json out.json

# scaled tiers
python3 evals/retrieval-quality/scale_workspace.py --seed-workspace evals/retrieval-quality/seed \
  --target-nodes 1000 --rng-seed 7 --out /tmp/tier1000
```

Hosted adapters need `GEMINI_API_KEY` (gemini-*), `GOOGLE_API_KEY` (mem0), and
`GBRAIN_HOME` pointing at a brain initialised with
`gbrain init --pglite --non-interactive --path $GBRAIN_HOME/brain.pglite --embedding-model google:gemini-embedding-001 --embedding-dimensions 768`.

## What is not here

- Mem0 and GBrain at scaled tiers (not run; cross-tool claims rest on the seed
  tier by design)
- MemMachine (needs Docker; not run)
- Any confidence intervals: 40 direct queries, one query changes recall by 0.025
